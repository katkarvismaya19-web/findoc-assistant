"""Generate a demo corpus of synthetic regulatory circulars.

The project ships with these already built in data/pdfs/, so it runs the
moment you unzip it - no downloading, no network.

These documents are INVENTED. They imitate the structure and register of
Indian banking circulars (numbered clauses, defined terms, circular
references, stated time periods) so the retrieval problem is realistic, but
no clause is real regulation and none should be relied on.

Before deploying publicly, swap in real documents:
    python -m scripts.fetch_corpus --limit 30
    python -m app.ingest --chunk-size 1000 --overlap 150 --collection findoc_1000

Regenerate the demo set with:
    python -m scripts.make_demo_corpus
"""
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "pdfs"

BANNER = (
    "SYNTHETIC DEMO DOCUMENT - not an actual regulatory publication. "
    "Generated for testing retrieval quality."
)

DOCS = [
    {
        "file": "demo-kyc-directions.pdf",
        "ref": "DEMO.AML.REC.14/14.01.001/2025-26",
        "title": "Customer Identification and Periodic Updation Directions",
        "clauses": [
            ("Applicability", "These directions apply to all regulated entities, including commercial banks, payments banks, small finance banks, non-banking financial companies and prepaid payment instrument issuers. They take effect from the first day of the quarter following publication."),
            ("Risk categorisation", "Every regulated entity shall categorise each customer as low risk, medium risk or high risk at the time of onboarding. The categorisation shall be reviewed whenever the transaction pattern of the account changes materially, and in any case at intervals not exceeding twelve months."),
            ("Periodic updation of records", "Periodic updation of customer identification records shall be carried out at least once every two years for customers categorised as high risk, once every eight years for medium risk customers, and once every ten years for low risk customers. The period shall be reckoned from the date of the last completed updation."),
            ("Self declaration", "Where there is no change in customer information, a self declaration to that effect obtained through a registered email address, registered mobile number, automated teller machine, internet banking or mobile application shall be sufficient to complete the periodic updation. A branch visit shall not be insisted upon."),
            ("Change of address", "Where the only change is in the address of the customer, the revised address may be furnished through any of the channels specified in clause 4. The regulated entity shall verify the declared address within two months of receiving the declaration."),
            ("Enhanced due diligence", "Enhanced due diligence shall be applied to customers categorised as high risk, to politically exposed persons and their family members, and to accounts of non face to face customers opened without in person verification. Enhanced due diligence shall include obtaining the source of funds and approval by an officer not below the rank of senior manager."),
            ("Consequence of non compliance", "Where a customer does not provide the documentation required for periodic updation within the stipulated period, the regulated entity may impose partial freezing of the account after issuing three notices, of which at least one shall be sent by registered post. Partial freezing shall not be imposed before the expiry of six months from the first notice."),
            ("Record retention", "Records of transactions and of customer identification shall be preserved for a period of five years from the date of the transaction or from the date of cessation of the business relationship, whichever is later."),
        ],
    },
    {
        "file": "demo-failed-transaction-turnaround.pdf",
        "ref": "DEMO.PSS.REC.08/02.14.003/2025-26",
        "title": "Harmonisation of Turnaround Time for Failed Transactions",
        "clauses": [
            ("Scope", "This circular prescribes the turnaround time for resolution of failed transactions across electronic payment systems and the compensation payable where the prescribed time is exceeded."),
            ("Automated teller machine transactions", "Where an account has been debited but cash has not been dispensed, the amount shall be reversed within five calendar days from the date of the transaction. Failure to reverse within this period attracts compensation of one hundred rupees per day of delay, computed from the sixth day."),
            ("Card to card transfers", "Where an account has been debited but the beneficiary card has not been credited, the debit shall be reversed within one calendar day from the date of the transaction. Compensation of one hundred rupees per day applies from the second day."),
            ("Immediate payment service", "Where an account has been debited but the beneficiary account has not been credited, and the transaction is not reversed automatically, the debit shall be reversed within one calendar day. Compensation applies from the second day."),
            ("Unified payment interface", "For person to person transactions where the beneficiary account is not credited, the debit shall be reversed within one calendar day. For person to merchant transactions the same period applies from the date on which the merchant confirms non delivery."),
            ("Point of sale transactions", "Where an account has been debited without generation of a charge slip, the debit shall be reversed within five calendar days. Compensation of one hundred rupees per day applies thereafter."),
            ("Compensation without claim", "Compensation payable under this circular shall be credited to the account of the customer without any claim being lodged. The absence of a complaint shall not relieve the regulated entity of the obligation to pay compensation."),
            ("Reporting", "Regulated entities shall report the number of failed transactions and the compensation paid in the quarterly return prescribed under the payment systems reporting framework, within fifteen days of the close of each quarter."),
        ],
    },
    {
        "file": "demo-digital-lending-guidelines.pdf",
        "ref": "DEMO.CRE.REC.22/21.04.048/2025-26",
        "title": "Guidelines on Digital Lending and Lending Service Providers",
        "clauses": [
            ("Definitions", "For the purposes of these guidelines, a digital lending application means a mobile or web based application used to facilitate lending. A lending service provider means an agent engaged by a regulated entity to carry out one or more functions of the lending process on its behalf."),
            ("Direct disbursal", "All loan disbursals and repayments shall be executed only between the bank account of the borrower and the bank account of the regulated entity. No pass through or pool account of a lending service provider or of any third party shall be used."),
            ("Fees to service providers", "Any fee payable to a lending service provider shall be paid directly by the regulated entity and shall not be charged to the borrower. The borrower shall not be required to make any payment to the lending service provider."),
            ("Key fact statement", "A key fact statement shall be provided to the borrower before execution of the loan contract. It shall disclose the annual percentage rate, the recovery mechanism, the details of the grievance redressal officer, and the cooling off period."),
            ("Cooling off period", "Borrowers shall be given a cooling off period of three days for loans with a tenor of seven days or more, and of one day for loans with a shorter tenor. During this period the borrower may exit the loan by repaying the principal and the proportionate annual percentage rate without penalty."),
            ("Credit limit increases", "Automatic increases in credit limit without the explicit prior consent of the borrower are prohibited. Consent recorded through a pre ticked checkbox shall not constitute explicit consent."),
            ("Data collection", "Data collected by digital lending applications shall be need based, shall be collected with the prior explicit consent of the borrower, and shall carry a clear audit trail. Access to the mobile phone resources of the borrower, including the contact list, the call log, the media files and the file library, is prohibited."),
            ("Grievance redressal", "A grievance redressal officer shall be designated for complaints relating to digital lending. Where a complaint is not resolved within thirty days, the complainant may approach the ombudsman under the integrated ombudsman scheme."),
        ],
    },
    {
        "file": "demo-atm-cash-replenishment.pdf",
        "ref": "DEMO.AUT.REC.12/24.01.041/2025-26",
        "title": "Cash Replenishment and Availability at Automated Teller Machines",
        "clauses": [
            ("Objective", "This circular prescribes standards for cash availability at automated teller machines and the scheme of penalties for cash outs, in order to reduce inconvenience to members of the public."),
            ("Cash out defined", "A cash out means a situation in which an automated teller machine remains out of cash for a period exceeding ten hours in a calendar month. The period shall be computed on the basis of the switch logs maintained by the operator."),
            ("Penalty for cash out", "A flat penalty of ten thousand rupees shall be levied for each automated teller machine in respect of each instance of cash out. The penalty shall be levied on the entity that owns the machine, irrespective of whether replenishment is outsourced."),
            ("White label machines", "In the case of white label automated teller machines, the penalty shall be recovered from the sponsor bank, which may in turn recover it from the operator under the terms of their commercial arrangement."),
            ("Monthly reporting", "Operators shall submit a system generated statement of cash out instances for each machine by the fifth day of the following month. Manual certification shall not be accepted in place of the system generated statement."),
            ("Cassette swap", "Replenishment of automated teller machines shall be carried out only through the cassette swap method. Open cash top up at the machine site is prohibited on account of the risk of pilferage and of dispute over shortages."),
            ("Downtime other than cash", "Downtime arising from causes other than absence of cash, including network failure and hardware fault, shall be recorded separately and shall not be counted towards the cash out computation."),
        ],
    },
    {
        "file": "demo-customer-grievance-redressal.pdf",
        "ref": "DEMO.CEP.REC.31/13.01.013/2025-26",
        "title": "Framework for Customer Grievance Redressal",
        "clauses": [
            ("Internal ombudsman", "Every regulated entity having more than ten banking outlets shall appoint an internal ombudsman. The internal ombudsman shall be a retired or serving officer not below the rank of deputy general manager, and shall not have been employed by the appointing entity in the preceding two years."),
            ("Reference of complaints", "All complaints that are proposed to be rejected in whole or in part shall be referred to the internal ombudsman before the decision is communicated to the complainant. Complaints relating to fraud, forgery and matters pending before a court are excluded from this requirement."),
            ("Time limit", "The internal ombudsman shall decide a reference within twenty one days. Where the recommendation of the internal ombudsman is not accepted by the regulated entity, approval of an officer of the rank of executive director or above shall be obtained."),
            ("Acknowledgement of complaints", "Every complaint shall be acknowledged within three working days of receipt, and shall be assigned a unique complaint identification number which shall be communicated to the complainant."),
            ("Resolution timeline", "A complaint shall be resolved within thirty days of receipt. Where a complaint requires investigation involving a third party, the complainant shall be informed of the expected timeline before the expiry of thirty days."),
            ("Root cause analysis", "The regulated entity shall carry out a root cause analysis of complaints on a quarterly basis, and shall place the analysis before the customer service committee of the board."),
            ("Display of information", "The name, address and contact particulars of the ombudsman having jurisdiction shall be displayed prominently at every banking outlet and on the website and mobile application of the regulated entity."),
        ],
    },
    {
        "file": "demo-cyber-security-framework.pdf",
        "ref": "DEMO.CSITE.REC.05/31.01.015/2025-26",
        "title": "Cyber Security Framework for Regulated Entities",
        "clauses": [
            ("Board approved policy", "Every regulated entity shall put in place a cyber security policy approved by its board, distinct from the broader information technology policy, and shall review it at least once every financial year."),
            ("Incident reporting", "All unusual cyber security incidents, whether or not they resulted in loss, shall be reported within six hours of detection. The report shall include the nature of the incident, the systems affected, and the containment measures taken."),
            ("Security operations centre", "Regulated entities shall establish a security operations centre providing continuous surveillance. The centre shall be operational at all times and shall maintain logs for a period of not less than one year."),
            ("Vulnerability assessment", "A vulnerability assessment and penetration test shall be conducted at least once every six months for critical systems, and after every material change to the application architecture."),
            ("Access control", "Privileged access shall be granted on the principle of least privilege and shall be reviewed once every quarter. Shared administrative credentials are prohibited."),
            ("Vendor risk", "Where information technology services are outsourced, the regulated entity shall remain responsible for the confidentiality and integrity of customer data. The outsourcing agreement shall provide for the right to audit the vendor."),
            ("Business continuity", "A disaster recovery drill shall be conducted at least once every six months, and the recovery time objective and recovery point objective shall be documented and tested."),
        ],
    },
    {
        "file": "demo-prepaid-payment-instruments.pdf",
        "ref": "DEMO.PPI.REC.19/02.14.006/2025-26",
        "title": "Directions on Prepaid Payment Instruments",
        "clauses": [
            ("Classification", "Prepaid payment instruments shall be classified as small instruments issued after obtaining minimum details of the holder, and as full instruments issued after completing customer due diligence."),
            ("Small instrument limits", "The amount loaded in a small prepaid payment instrument shall not exceed ten thousand rupees in any month, and the total amount loaded during a financial year shall not exceed one lakh twenty thousand rupees. The outstanding balance shall not exceed ten thousand rupees at any time."),
            ("Conversion", "A small prepaid payment instrument shall be converted into a full instrument within twenty four months of issue, failing which no further credit shall be permitted, although the holder may continue to use the existing balance."),
            ("Full instrument limits", "The outstanding balance in a full prepaid payment instrument shall not exceed two lakh rupees at any point of time. Funds transfer from a full instrument shall be permitted up to two lakh rupees per month per holder."),
            ("Interoperability", "Prepaid payment instruments in the form of wallets shall be made interoperable through the unified payments interface. Instruments in the form of cards shall be interoperable through the card networks."),
            ("Validity and forfeiture", "Prepaid payment instruments shall have a minimum validity of one year from the date of last loading. The holder shall be given a reminder at least forty five days before expiry. The outstanding balance shall not be forfeited without such reminder."),
            ("Escrow account", "Non bank issuers shall maintain the outstanding balance in an escrow account with a scheduled commercial bank. No other amount shall be credited to the escrow account."),
        ],
    },
    {
        "file": "demo-priority-sector-lending.pdf",
        "ref": "DEMO.FIDD.REC.27/04.09.001/2025-26",
        "title": "Priority Sector Lending Targets and Classification",
        "clauses": [
            ("Overall target", "The overall priority sector lending target for domestic commercial banks shall be forty per cent of adjusted net bank credit or of the credit equivalent of off balance sheet exposure, whichever is higher."),
            ("Agriculture sub target", "Within the overall target, a sub target of eighteen per cent shall apply to agriculture. Of this, a sub target of ten per cent shall apply to small and marginal farmers."),
            ("Micro enterprises", "A sub target of seven and one half per cent shall apply to micro enterprises. Lending to a micro enterprise shall be reckoned under this sub target irrespective of the amount of the loan."),
            ("Weaker sections", "A sub target of twelve per cent shall apply to weaker sections. The categories comprising weaker sections shall include small and marginal farmers, artisans, beneficiaries of government sponsored schemes, and self help groups."),
            ("Computation", "Compliance shall be computed on the basis of the average of the priority sector target achievement at the close of each quarter of the financial year, and not on the position as at the close of the year alone."),
            ("Shortfall", "Where a bank falls short of the target, it shall contribute the amount of the shortfall to a fund notified for the purpose. The contribution shall be made within one month of the close of the financial year."),
            ("Certificates", "Priority sector lending certificates may be purchased to meet a shortfall. The certificates shall be valid until the thirty first day of March of the year in which they are issued, irrespective of the date of issue."),
        ],
    },
    {
        "file": "demo-locker-facility-revised.pdf",
        "ref": "DEMO.LEG.REC.41/09.07.005/2025-26",
        "title": "Revised Instructions on Safe Deposit Locker Facility",
        "clauses": [
            ("Model agreement", "Banks shall execute a revised locker agreement with each existing locker holder in the form prescribed by the Indian Banks Association. The agreement shall be executed on stamp paper, the cost of which shall be borne by the bank."),
            ("Liability of the bank", "Where loss of contents occurs on account of fire, theft, building collapse, or fraud committed by an employee of the bank, the liability of the bank shall be limited to one hundred times the prevailing annual rent of the locker."),
            ("Exclusion of liability", "The bank shall not be liable for loss arising from an act of God, provided the bank has taken reasonable care of the premises. The onus of establishing such care shall rest with the bank."),
            ("Term deposit as security", "A bank may obtain a term deposit at the time of allotment covering three years of rent and the charges of breaking open the locker. A term deposit shall not be insisted upon from an existing locker holder as a condition of continuing the facility."),
            ("Access notification", "The bank shall send an email and a short message alert to the registered contact particulars of the locker holder at the close of the day on which the locker is accessed."),
            ("Dormant lockers", "Where a locker has not been operated for a period exceeding three years, the bank may break open the locker after issuing notice to the holder, irrespective of whether the rent has been paid regularly."),
            ("Waiting list", "Banks shall maintain a branch wise waiting list for locker allotment and shall issue an acknowledgement with a waiting number to every applicant."),
        ],
    },
    {
        "file": "demo-account-aggregator-framework.pdf",
        "ref": "DEMO.DOR.REC.36/03.10.123/2025-26",
        "title": "Account Aggregator Framework and Consent Architecture",
        "clauses": [
            ("Role of the aggregator", "An account aggregator shall act solely as a conduit for the transfer of financial information with the consent of the customer. It shall not store, process, analyse or use the financial information that passes through it."),
            ("Consent artefact", "Every transfer of financial information shall be preceded by a consent artefact recording the identity of the requesting entity, the purpose of the request, the types of information sought, the period for which the consent is valid, and the frequency of access."),
            ("Revocation", "A customer may revoke a consent at any time. Upon revocation the account aggregator shall communicate the revocation to the financial information provider and to the financial information user within one hour."),
            ("Data storage prohibition", "The account aggregator shall not store the financial information for any period longer than is necessary for the transfer, and in no case beyond the completion of the session."),
            ("Financial information provider", "A financial information provider shall transmit the requested information within one hour of receiving a valid request accompanied by a consent artefact, and shall not levy any charge on the customer for the transmission."),
            ("Audit trail", "An immutable audit trail of every consent granted, used and revoked shall be maintained for a period of not less than seven years."),
            ("Grievance", "Every account aggregator shall designate a grievance officer whose particulars shall be displayed on its application and website, and shall resolve complaints within thirty days."),
        ],
    },
]


class Circular(FPDF):
    def __init__(self, ref, title):
        super().__init__()
        self.ref = ref
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120)
        self.cell(0, 5, BANNER, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180)
        self.line(15, 18, 195, 18)
        self.ln(6)
        self.set_text_color(0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120)
        self.cell(0, 10, f"{self.ref}    Page {self.page_no()}", align="C")


def build(doc):
    pdf = Circular(doc["ref"], doc["title"])
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, doc["ref"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 7, doc["title"])
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        "In exercise of the powers conferred under the applicable statute, the "
        "following directions are issued. These directions shall come into force "
        "with immediate effect and shall supersede earlier instructions on the "
        "subject to the extent that they are inconsistent."
    )
    pdf.ln(5)

    for i, (heading, text) in enumerate(doc["clauses"], start=1):
        if pdf.get_y() > 235:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 6, f"{i}. {heading}")
        pdf.ln(1)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5.4, text)
        pdf.ln(4)

    dest = OUT / doc["file"]
    pdf.output(str(dest))
    return dest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Writing demo corpus to {OUT}\n")
    for doc in DOCS:
        dest = build(doc)
        print(f"  + {dest.name} ({dest.stat().st_size / 1024:.0f} KB)")
    print(f"\n{len(DOCS)} documents written.")
    print("These are synthetic. For the deployed version use real documents:")
    print("  python -m scripts.fetch_corpus --limit 30")


if __name__ == "__main__":
    main()
