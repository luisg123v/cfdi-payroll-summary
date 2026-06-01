# CFDI Payroll Summary

Generate a summary of Mexican payroll CFDIs for the SAT annual tax return.

This script reads Mexican payroll CFDI XML files containing the `Nomina`
complement and generates a YAML summary with the values requested by the
Mexican Tax Administration Service (SAT) in the annual tax return.

The summary includes the detail of each payroll receipt and annual totals
grouped by employer and CFDI emission year.

## Requirements

- Python 3.
- Payroll CFDI XML files containing the Mexican `Nomina` complement.
- Python dependencies:

  * `lxml`
  * `PyYAML`

## Usage

Place the payroll CFDI XML files in the same directory as the script:

```text
.
├── cfdi_payroll_summary.py
├── payroll_001.xml
├── payroll_002.xml
└── payroll_003.xml
```

Then run:

```bash
python3 cfdi_payroll_summary.py
```

The script will generate:

```text
payroll_summary.yaml
```

## Output

The output contains two main sections:

- `payslips`: detail of each processed payroll CFDI.
- `annual totals`: values grouped by employer and CFDI emission year.

Example:

```yaml
payslips:
  1 EXAMPLE EMPLOYER january q1:
    company name: EXAMPLE EMPLOYER
    emission date: '2025-02-14T23:59:00'
    date from: '2025-02-01'
    date to: '2025-02-15'
    serie: january
    folio: q1
    net: 12000.0
    income: 15000.0
    withheld tax: 2500.0
    employment subsidy: 0.0
    employment subsidy received: 0.0
    exempt: 500.0
    exempts:
      otros: 500.0
  2 EXAMPLE EMPLOYER january q2:
    ...
  3 EXAMPLE EMPLOYER february q1:
    ...

annual totals:
  EXAMPLE EMPLOYER 2025:
    income: 180000
    withheld tax: 30000
    employment subsidy: 0
    employment subsidy received: 0
    exempt: 6000
    exempts:
      aguinaldo: 2000
      PTU: 1000
      prima dominical: 0
      prima vacacional: 1500
      otros: 1500
```

Annual totals are rounded to integer values because the SAT annual tax return
requests amounts without decimals.

## Data Privacy

Payroll CFDI files may contain sensitive personal and fiscal information.

Do not commit real CFDI XML files or generated summaries to the repository.
The repository should ignore them, for example:

```gitignore
# Payroll summary and CFDIs
payroll_summary.yaml
*.xml
```

## Warning

The output should be reviewed before using it to fill official tax forms.

## License

This project may be distributed under the MIT License. See `LICENSE` for
details.
