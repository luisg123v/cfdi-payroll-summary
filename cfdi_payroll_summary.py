import glob
import sys
from collections import defaultdict

import yaml
from lxml import objectify

OUTPUT_FILENAME = "payroll_summary.yaml"

PERCEPTION_TYPES = {
    "002": "aguinaldo",
    "003": "PTU",
    "020": "prima dominical",
    "021": "prima vacacional",
}


def get_payslip_xmls():
    """Open all XML files and return them as XML objects, sorted by date"""
    xml_filenames = glob.glob("*.xml")
    xmls = [objectify.parse(fname).getroot() for fname in xml_filenames]
    xmls.sort(key=lambda x: x.get("Fecha"))
    return xmls


def safe_int(value):
    """Cast to integer when possible.

    useful for the serie and folio, so that the values don't need to be quoted.
    """
    if not value:
        return ""
    return int(value) if value.isdigit() and not value.startswith("0") else value


def get_payslip_as_dict(xml):
    """Get a dictionary representation of a payslip from its XML object"""
    node_payslip = xml.xpath("//*[local-name()='Nomina']")[0]
    node_perceptions = node_payslip.Percepciones
    nodes_employment_subsidy = xml.xpath(
        "//*[local-name()='OtroPago' and @TipoOtroPago='002']"
    )
    payslip = {
        "company name": xml.Emisor.get("Nombre"),
        "emission date": xml.get("Fecha"),
        "date from": node_payslip.get("FechaInicialPago"),
        "date to": node_payslip.get("FechaFinalPago"),
        "serie": safe_int(xml.get("Serie")),
        "folio": safe_int(xml.get("Folio")),
        "net": float(xml.get("Total")),
        "income": float(node_perceptions.get("TotalSueldos")),
        "withheld tax": (
            float(node_payslip.Deducciones.get("TotalImpuestosRetenidos"))
            if hasattr(node_payslip, "Deducciones")
            else 0.0
        ),
        "employment subsidy": sum(
            float(n.SubsidioAlEmpleo.get("SubsidioCausado"))
            for n in nodes_employment_subsidy
        ),
        "employment subsidy received": sum(
            float(n.get("Importe")) for n in nodes_employment_subsidy
        ),
        "exempt": float(node_perceptions.get("TotalExento")),
    }

    # Check if there are exemptions
    exempts = {}
    for node_perception in node_perceptions.getchildren():
        amount_perception_exempt = float(node_perception.get("ImporteExento"))
        if not amount_perception_exempt:
            continue

        perception_code = node_perception.get("TipoPercepcion")
        perception_name = PERCEPTION_TYPES.get(perception_code, "otros")
        exempts.setdefault(perception_name, 0.0)
        exempts[perception_name] += amount_perception_exempt

    if exempts:
        payslip["exempts"] = exempts
    return payslip


def sum_to_annual_totals(payslip, annual_totals):
    """Sum amounts of the provided payslip to annual totals"""
    annual_totals["income"] += payslip["income"]
    annual_totals["withheld tax"] += payslip["withheld tax"]
    annual_totals["exempt"] += payslip["exempt"]
    annual_totals["employment subsidy"] += payslip["employment subsidy"]
    annual_totals["employment subsidy received"] += payslip[
        "employment subsidy received"
    ]
    for exempt_name, exempt_amount in payslip.get("exempts", {}).items():
        annual_totals["exempts"][exempt_name] += exempt_amount


def round_floats(dictionary):
    """Round numeric values and cast them to integers"""
    for key, value in dictionary.items():
        if isinstance(value, float):
            dictionary[key] = int(round(value))
        elif isinstance(value, dict):
            round_floats(value)


def main():
    result = {
        "payslips": {},
        "annual totals": defaultdict(
            lambda: {
                "income": 0,
                "withheld tax": 0,
                "employment subsidy": 0,
                "employment subsidy received": 0,
                "exempt": 0,
                "exempts": {
                    **dict.fromkeys(PERCEPTION_TYPES.values(), 0),
                    "otros": 0,
                },
            }
        ),
    }
    xmls = get_payslip_xmls()
    if not xmls:
        print("No XML files were found, exiting.")
        sys.exit(1)

    for index, xml in enumerate(xmls, start=1):
        # Generate and add payslip
        payslip = get_payslip_as_dict(xml)
        payslip_name = (
            f"{index} %(company name)s %(serie)s %(folio)s" % payslip
        ).strip()
        result["payslips"][payslip_name] = payslip

        # Sum amounts to annual totals, grouped by company and year
        company_name = payslip["company name"]
        year = payslip["emission date"].split("-", 1)[0]
        annual_totals_this_payslip = result["annual totals"][f"{company_name} {year}"]
        sum_to_annual_totals(payslip, annual_totals_this_payslip)

    # Cast result to the correct data types:
    # - Round and cast totals to integers: The SAT expects numbers without decimals
    # - Cast defauldict to dict: Pyyaml doesn't serialize defaultdict
    round_floats(result["annual totals"])
    result["annual totals"] = dict(result["annual totals"])

    # Write the result
    yaml_str = yaml.safe_dump(result, sort_keys=False, allow_unicode=True).replace(
        "\nannual totals", "\n\nannual totals"
    )
    with open(OUTPUT_FILENAME, "w") as f_out:
        f_out.write(yaml_str)
    print("Summary generated:", OUTPUT_FILENAME)


if __name__ == "__main__":
    main()
