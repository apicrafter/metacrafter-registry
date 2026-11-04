# Microsoft Purview sensitive information types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#52](https://github.com/apicrafter/metacrafter-registry/issues/52).

The issue lists 305 sensitive information types (SITs) of Microsoft 365
compliance, now Microsoft Purview, and asks to link each one to the registry.
18 items were already ticked.

Source reviewed: the SIT pages on learn.microsoft.com
(`https://learn.microsoft.com/en-us/purview/sit-defn-<name>`), fetched on
2026-11-04. Every item of the issue was read: name, format, pattern, checksum
flag and keywords. The issue links "Australia company number" to the business
number page by mistake; the review used `sit-defn-australia-company-number`.

## Summary

- **The link is the existing crosswalk key `mappings.purview`.** It holds
  Purview type names. 223 records now carry it; 62 did before this change.
- **Lookup ignores case, periods and apostrophes.** Microsoft writes the same
  type as "U.S. driver's license number" and "U.S. Drivers License Number".
  `crosswalk("purview", ...)` now treats such names as equal.
- **Mapped to existing records:** 47 records got their first Purview mapping,
  for example `cnpj`, `hr_oib`, `it_iva`, `ro_cnp`, `ukdriverlic` and
  `address`.
- **New draft records: 114.**
  - 88 national identifiers: driver's licences, passports (as patterns of
    `passport`), identity cards, personal, tax and health numbers.
  - 4 bank account numbers, as patterns of `bankaccount`.
  - 13 secrets in a new category `secrets`.
  - 7 medical vocabularies, such as `medical_condition` and
    `medication_generic_name`.
  - 1 Indian GST number, 1 Luxembourg legal entity number.
- **New tool record `microsoftpurview`.** Its `supported_types` are all
  records with a Purview mapping, and a test keeps the two in step.
- **Not linked: 2 types.** See [Not linked](#not-linked).

## How the mapping is written

`mappings.purview` lists, in this order:

1. The current name of the type, as the title of its Microsoft page.
2. The name used in the issue, when Microsoft renamed the type since. For
   example "Microsoft Entra client secret" was "Azure AD client secret", and
   "German Passport Number" was "Germany passport number". Old names keep
   resolving.
3. The bundles the type belongs to. Purview groups types into bundles: "EU
   passport number", "EU national identification number", "EU drivers license
   number", "EU Social Security Number (SSN) or Equivalent ID", "EU Tax
   Identification Number (TIN)", "All Credential Types" and "All medical terms
   and conditions". Each bundle page lists its members. The bundle name is
   added to every member's records, so
   `crosswalk("purview", "EU passport number")` returns the 27 passport
   records of the bundle.

Names that already were in the data and that are not in the issue stay, for
example "Russia taxpayer identification number" on `inn`.

## Match types

The table below gives each type a match type:

- **exact**: the record means the same thing as the Purview type.
- **close**: the same values, but the Purview type is defined differently:
  - "Netherlands tax identification number" is `bsn`: the citizen service
    number is the Dutch TIN of individuals.
  - "Sweden tax identification number" is `sepersonnummer`, for the same
    reason.
  - "Poland tax identification number" is `plpesel`. Microsoft describes 11
    digits with a check digit. That is a PESEL, which Poland uses as the TIN of
    individuals; the NIP (`plnip`) has 10 digits.
  - "Canada health service number" is `cabcphn`. Microsoft describes ten
    digits with the keyword "personal health number", which is the British
    Columbia PHN.
  - "Japan social insurance number (SIN)" is `jp_pension_number`. Microsoft's
    pattern (four digits, a hyphen, six digits) is the basic pension number.
    The keywords also cover health and employment insurance numbers.
  - "International classification of diseases (ICD-10-CM)" is `icd10` and
    `medical_condition`. Purview looks for ICD-10-CM codes and for the
    descriptions of the codes. ICD-10-CM is the US clinical modification of
    ICD-10.
  - "Luxembourg National Identification Number (Non-natural persons)" is the
    new `lu_matricule_entity`. Microsoft files it under tax numbers.
- **broader**: the record is a wider concept:
  - The 39 country "physical addresses" types map to `address`. They describe
    no format of their own.
  - Most credential types are specific to one Azure service. They map to
    generic records: `api_key`, `access_token`, `symmetric_key`,
    `shared_access_signature`, `connection_string`, `password` and
    `user_credentials`. Separate records exist only for formats that identify
    the issuer: `github_token`, `google_api_key`, `slack_token`,
    `aws_secret_access_key` and `azure_storage_account_key`.
  - "Impairments Listed In The U.S. Disability Evaluation Under Social
    Security" and "International classification of diseases (ICD-9-CM)" map
    to `medical_condition`, "Blood test terms" to `lab_test`.
- **bundle**: see above.

## New records

All new records are `status: draft`. Their sources and limits:

- **Formats come from Microsoft.** Each record links its Microsoft page as a
  `doc` link. The regexps describe what Purview looks for, not always the
  issuer's full rules. For example, Purview describes the Austrian driver's
  licence number only as eight digits. Review each record against the issuing
  authority before you mark it `stable`.
- **No `checksum`.** Microsoft marks many of these types as having a check
  digit, for example `hu_taj`, `si_emso`, `tw_national_id`, `za_id` and
  `lv_personal_code`. The registry has no algorithm for them yet.
- **Few examples.** Microsoft publishes no sample values, and the registry does
  not accept made-up ones. Only `us_mbi` has examples: the format example that
  CMS publishes and a negative example.
- **Wording.** Descriptions are written for the registry. Names follow the
  registry's style ("Austrian driver's license number", ids such as
  `at_driver_license`).
- **Reference lists.** New countries: HK, PH, QA, SI, SK, TW, UA, ZA. New
  languages: sk, sl, uk. New category: `secrets`.
- **Medical parents.** `rumedmnn` now has the parent `medication_generic_name`,
  and `rumedicinetradename` has the parent `medication_brand_name`.

## Not linked

- **Austria identity card.** Microsoft describes a 24-character value made of
  letters, digits, slashes, plus and equals signs. That is an encoded
  identifier, not the number printed on the card. A record should wait until
  the format is confirmed from an Austrian source.
- **Lifestyles that relate to medical conditions.** A dictionary of habits
  such as smoking and alcohol use. It is not a value type the registry can
  describe.

## Recommendations and follow-ups

- **20 newer types.** The Microsoft index now lists 20 types that are not in
  the issue. Several have registry records already:
  - Russia taxpayer identification number: `inn`, already mapped
  - UAE identity card number: `aeemiratesid`, already mapped
  - UAE passport number: `aepassport`
  - Indonesia driver's license and passport numbers: `iddriverlic`,
    `idpassport`
  - South Korea driver's license and passport numbers: `krdriverlic`,
    `krpassport`
  - Colombia tax identification number: `co_nit`
  - China, Greenland, Russia, Singapore, South Africa and Ukraine physical
    addresses: `address`
  - Others need new records: Colombia national ID, Ecuador unique
    identification number, Malaysia passport, Philippines national ID,
    Singapore driver's license and passport.
- **Check-digit algorithms** for the national numbers above, so that
  `identify` can use them.
- **Review the drafts** country by country, adding examples from official
  specimens where they exist.

## Mapping table

All 305 types of the issue. "New record" marks types linked to a record that
this change creates.

| Purview type | Registry record | Match | New record |
|---|---|---|---|
| [ABA Routing Number](https://learn.microsoft.com/en-us/purview/sit-defn-aba-routing) | `abaroutingnum` | exact |  |
| [All Credential Types](https://learn.microsoft.com/en-us/purview/sit-defn-all-creds) (issue: All credentials) | its members | bundle |  |
| [All full names](https://learn.microsoft.com/en-us/purview/sit-defn-all-full-names) | `person_fullname` | exact |  |
| [All medical terms and conditions](https://learn.microsoft.com/en-us/purview/sit-defn-all-medical-terms-conditions) | its members | bundle |  |
| [All Physical Addresses](https://learn.microsoft.com/en-us/purview/sit-defn-all-physical-addresses) | `address` | exact |  |
| [Amazon S3 client secret access key](https://learn.microsoft.com/en-us/purview/sit-defn-amazon-s3-client-secret-access-key) | `aws_secret_access_key` | exact | yes |
| [Argentina national identity (DNI) number](https://learn.microsoft.com/en-us/purview/sit-defn-argentina-national-identity-numbers) | `ardni` | exact |  |
| [Argentina Unique Tax Identification Key (CUIT/CUIL)](https://learn.microsoft.com/en-us/purview/sit-defn-argentina-unique-tax-identification-key) | `cuit` | exact |  |
| [ASP.NET machine key](https://learn.microsoft.com/en-us/purview/sit-defn-asp-net-machine-key) | `symmetric_key` | broader | yes |
| [Australia bank account number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-bank-account-number) | `au_bank_account` | exact | yes |
| [Australia company number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-company-number) | `auacn` | exact |  |
| [Australia Driver's License Number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-drivers-license-number) | `au_driver_license` | exact | yes |
| [Australia medical account number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-medical-account-number) | `aumedicarenum`, `medicare` | exact |  |
| [Australia passport number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-passport-number) | `aupassport` | exact |  |
| [Australia physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-australia-physical-addresses) | `address` | broader |  |
| [Australia tax file number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-tax-file-number) | `autfn`, `tfn` | exact |  |
| [Australian Business Number](https://learn.microsoft.com/en-us/purview/sit-defn-australia-business-number) (issue: Australia business number) | `auabn`, `abn` | exact |  |
| [Austria Driver's License Number](https://learn.microsoft.com/en-us/purview/sit-defn-austria-drivers-license-number) | `at_driver_license` | exact | yes |
| [Austria identity card](https://learn.microsoft.com/en-us/purview/sit-defn-austria-identity-card) | - | not linked |  |
| [Austria passport number](https://learn.microsoft.com/en-us/purview/sit-defn-austria-passport-number) | `at_passport` | exact | yes |
| [Austria physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-austria-physical-addresses) | `address` | broader |  |
| [Austria social security number](https://learn.microsoft.com/en-us/purview/sit-defn-austria-social-security-number) | `at_vnr` | exact |  |
| [Austria tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-austria-tax-identification-number) | `at_tin` | exact | yes |
| [Austria Value Added Tax (VAT) Number](https://learn.microsoft.com/en-us/purview/sit-defn-austria-value-added-tax) (issue: Austria value added tax) | `at_vat` | exact |  |
| [Azure App Service deployment password](https://learn.microsoft.com/en-us/purview/sit-defn-azure-app-service-deployment-password) | `password` | broader |  |
| [Azure Batch Shared Access Key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-batch-shared-access-key) | `symmetric_key` | broader | yes |
| [Azure Bot Framework secret key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-bot-framework-secret-key) | `api_key` | broader | yes |
| [Azure Bot service app secret](https://learn.microsoft.com/en-us/purview/sit-defn-azure-bot-service-app-secret) | `api_key` | broader | yes |
| [Azure Cognitive Search API key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-cognitive-search-api-key) | `api_key` | broader | yes |
| [Azure Cognitive Service key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-cognitive-service-key) | `api_key` | broader | yes |
| [Azure Container Registry access key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-container-registry-access-key) | `symmetric_key` | broader | yes |
| [Azure Cosmos DB account access key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-cosmos-db-account-access-key) | `symmetric_key` | broader | yes |
| [Azure Databricks personal access token](https://learn.microsoft.com/en-us/purview/sit-defn-azure-databricks-personal-access-token) | `access_token` | broader | yes |
| [Azure DevOps app secret](https://learn.microsoft.com/en-us/purview/sit-defn-azure-devops-app-secret) | `api_key` | broader | yes |
| [Azure DevOps personal access token](https://learn.microsoft.com/en-us/purview/sit-defn-azure-devops-personal-access-token) | `access_token` | broader | yes |
| [Azure DocumentDB auth key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-document-db-auth-key) | `connection_string` | broader | yes |
| [Azure EventGrid access key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-eventgrid-access-key) | `symmetric_key` | broader | yes |
| [Azure Function Master / API key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-function-master-api-key) | `api_key` | broader | yes |
| [Azure IAAS database connection string and Azure SQL connection string](https://learn.microsoft.com/en-us/purview/sit-defn-azure-iaas-database-connection-string-azure-sql-connection-string) | `connection_string` | broader | yes |
| [Azure IoT connection string](https://learn.microsoft.com/en-us/purview/sit-defn-azure-iot-connection-string) | `connection_string` | broader | yes |
| [Azure IoT shared access key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-iot-shared-access-key) | `symmetric_key` | broader | yes |
| [Azure Logic App shared access signature](https://learn.microsoft.com/en-us/purview/sit-defn-azure-logic-app-shared-access-signature) | `shared_access_signature` | broader | yes |
| [Azure Machine Learning web service API key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-machine-learning-web-service-api-key) | `api_key` | broader | yes |
| [Azure Maps subscription key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-maps-subscription-key) | `api_key` | broader | yes |
| [Azure publish setting password](https://learn.microsoft.com/en-us/purview/sit-defn-azure-publish-setting-password) | `password` | broader |  |
| [Azure Redis cache connection string](https://learn.microsoft.com/en-us/purview/sit-defn-azure-redis-cache-connection-string) | `connection_string` | broader | yes |
| [Azure Redis cache connection string password](https://learn.microsoft.com/en-us/purview/sit-defn-azure-redis-cache-connection-string-password) | `password` | broader |  |
| [Azure SAS](https://learn.microsoft.com/en-us/purview/sit-defn-azure-sas) | `shared_access_signature` | exact | yes |
| [Azure service bus connection string](https://learn.microsoft.com/en-us/purview/sit-defn-azure-service-bus-connection-string) | `connection_string` | broader | yes |
| [Azure service bus shared access signature](https://learn.microsoft.com/en-us/purview/sit-defn-azure-service-bus-shared-access-signature) | `shared_access_signature` | broader | yes |
| [Azure Shared Access key / Web Hook token](https://learn.microsoft.com/en-us/purview/sit-defn-azure-shared-access-key-web-hook-token) | `symmetric_key` | broader | yes |
| [Azure SignalR access key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-signalr-access-key) | `symmetric_key` | broader | yes |
| [Azure SQL connection string](https://learn.microsoft.com/en-us/purview/sit-defn-azure-sql-connection-string) | `connection_string` | broader | yes |
| [Azure storage account access key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-storage-account-access-key) | `azure_storage_account_key` | exact | yes |
| [Azure storage account key](https://learn.microsoft.com/en-us/purview/sit-defn-azure-storage-account-key) | `connection_string` | broader | yes |
| [Azure Storage account key (generic)](https://learn.microsoft.com/en-us/purview/sit-defn-azure-storage-account-key-generic) | `azure_storage_account_key` | exact | yes |
| [Azure Storage account shared access signature](https://learn.microsoft.com/en-us/purview/sit-defn-azure-storage-account-shared-access-signature) | `shared_access_signature` | broader | yes |
| [Azure Storage account shared access signature for high risk resources](https://learn.microsoft.com/en-us/purview/sit-defn-azure-storage-account-shared-access-signature-high-risk-resources) | `shared_access_signature` | broader | yes |
| [Azure subscription management certificate](https://learn.microsoft.com/en-us/purview/sit-defn-azure-subscription-management-certificate) | `x509_private_key` | broader | yes |
| [Belgium drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-belgium-drivers-license-number) | `be_driver_license` | exact | yes |
| [Belgium national number](https://learn.microsoft.com/en-us/purview/sit-defn-belgium-national-number) | `benatcardid` | exact |  |
| [Belgium passport number](https://learn.microsoft.com/en-us/purview/sit-defn-belgium-passport-number) | `be_passport` | exact | yes |
| [Belgium physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-belgium-physical-addresses) | `address` | broader |  |
| [Belgium value added tax number](https://learn.microsoft.com/en-us/purview/sit-defn-belgium-value-added-tax-number) | `be_vat` | exact |  |
| [Blood test terms](https://learn.microsoft.com/en-us/purview/sit-defn-blood-test-terms) | `lab_test` | broader | yes |
| [Brand medication names](https://learn.microsoft.com/en-us/purview/sit-defn-brand-medication-names) | `medication_brand_name` | exact | yes |
| [Brazil CPF number](https://learn.microsoft.com/en-us/purview/sit-defn-brazil-cpf-number) | `cpf`, `brcpf` | exact |  |
| [Brazil legal entity number (CNPJ)](https://learn.microsoft.com/en-us/purview/sit-defn-brazil-legal-entity-number) | `cnpj` | exact |  |
| [Brazil National ID Card (RG)](https://learn.microsoft.com/en-us/purview/sit-defn-brazil-national-identification-card) (issue: Brazil national identification card (RG)) | `rg` | exact |  |
| [Brazil physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-brazil-physical-addresses) | `address` | broader |  |
| [Bulgaria drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-bulgaria-drivers-license-number) | `bg_driver_license` | exact | yes |
| [Bulgaria passport number](https://learn.microsoft.com/en-us/purview/sit-defn-bulgaria-passport-number) | `bg_passport` | exact | yes |
| [Bulgaria physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-bulgaria-physical-addresses) | `address` | broader |  |
| [Bulgaria uniform civil number](https://learn.microsoft.com/en-us/purview/sit-defn-bulgaria-uniform-civil-number) | `bg_egn` | exact |  |
| [Canada bank account number](https://learn.microsoft.com/en-us/purview/sit-defn-canada-bank-account-number) | `ca_bank_account` | exact | yes |
| [Canada drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-canada-drivers-license-number) | `cadriverlic` | exact |  |
| [Canada health service number](https://learn.microsoft.com/en-us/purview/sit-defn-canada-health-service-number) | `cabcphn` | close |  |
| [Canada passport number](https://learn.microsoft.com/en-us/purview/sit-defn-canada-passport-number) | `capassport` | exact |  |
| [Canada personal health identification number (PHIN)](https://learn.microsoft.com/en-us/purview/sit-defn-canada-personal-health-identification-number) | `ca_phin` | exact | yes |
| [Canada physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-canada-physical-addresses) | `address` | broader |  |
| [Canada social insurance number](https://learn.microsoft.com/en-us/purview/sit-defn-canada-social-insurance-number) | `casin` | exact |  |
| [Chile identity card number](https://learn.microsoft.com/en-us/purview/sit-defn-chile-identity-card-number) | `cl_rut` | exact |  |
| [China resident identity card (PRC) number](https://learn.microsoft.com/en-us/purview/sit-defn-china-resident-identity-card-number) | `idcard` | exact |  |
| [Client secret / API key](https://learn.microsoft.com/en-us/purview/sit-defn-client-secret-api-key) | `api_key` | exact | yes |
| [Credit card number](https://learn.microsoft.com/en-us/purview/sit-defn-credit-card-number) | `bankcard` | exact |  |
| [Croatia drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-croatia-drivers-license-number) | `hr_driver_license` | exact | yes |
| [Croatia identity card number](https://learn.microsoft.com/en-us/purview/sit-defn-croatia-identity-card-number) | `hr_id_card` | exact | yes |
| [Croatia passport number](https://learn.microsoft.com/en-us/purview/sit-defn-croatia-passport-number) | `hr_passport` | exact | yes |
| [Croatia personal identification (OIB) number](https://learn.microsoft.com/en-us/purview/sit-defn-croatia-personal-identification-number) | `hr_oib` | exact |  |
| [Croatia physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-croatia-physical-addresses) | `address` | broader |  |
| [Cyprus Driver's License Number](https://learn.microsoft.com/en-us/purview/sit-defn-cyprus-drivers-license-number) | `cy_driver_license` | exact | yes |
| [Cyprus identity card](https://learn.microsoft.com/en-us/purview/sit-defn-cyprus-identity-card) | `cy_id_card` | exact | yes |
| [Cyprus passport number](https://learn.microsoft.com/en-us/purview/sit-defn-cyprus-passport-number) | `cy_passport` | exact | yes |
| [Cyprus physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-cyprus-physical-addresses) | `address` | broader |  |
| [Cyprus tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-cyprus-tax-identification-number) | `cy_tin` | exact | yes |
| [Czech drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-czech-drivers-license-number) | `cz_driver_license` | exact | yes |
| [Czech passport number](https://learn.microsoft.com/en-us/purview/sit-defn-czech-passport-number) | `cz_passport` | exact | yes |
| [Czech personal identity number](https://learn.microsoft.com/en-us/purview/sit-defn-czech-personal-identity-number) | `cz_rc` | exact |  |
| [Czech Republic physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-czech-republic-physical-addresses) | `address` | broader |  |
| [Denmark drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-denmark-drivers-license-number) | `dk_driver_license` | exact | yes |
| [Denmark passport number](https://learn.microsoft.com/en-us/purview/sit-defn-denmark-passport-number) | `dk_passport` | exact | yes |
| [Denmark personal identification number](https://learn.microsoft.com/en-us/purview/sit-defn-denmark-personal-identification-number) | `dkcprnum` | exact |  |
| [Denmark physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-denmark-physical-addresses) | `address` | broader |  |
| [Diseases](https://learn.microsoft.com/en-us/purview/sit-defn-diseases) | `medical_condition` | exact | yes |
| [Drug Enforcement Agency (DEA) number](https://learn.microsoft.com/en-us/purview/sit-defn-drug-enforcement-agency-number) | `usdeanumber` | exact |  |
| [Estonia drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-estonia-drivers-license-number) | `ee_driver_license` | exact | yes |
| [Estonia passport number](https://learn.microsoft.com/en-us/purview/sit-defn-estonia-passport-number) | `ee_passport` | exact | yes |
| [Estonia personal identification code](https://learn.microsoft.com/en-us/purview/sit-defn-estonia-personal-identification-code) | `ee_ik` | exact |  |
| [Estonia physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-estonia-physical-addresses) | `address` | broader |  |
| [EU debit card number](https://learn.microsoft.com/en-us/purview/sit-defn-eu-debit-card-number) | `bankcard` | exact |  |
| [EU drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-eu-drivers-license-number) | its members | bundle |  |
| [EU national identification number](https://learn.microsoft.com/en-us/purview/sit-defn-eu-national-identification-number) | its members | bundle |  |
| [EU passport number](https://learn.microsoft.com/en-us/purview/sit-defn-eu-passport-number) | its members | bundle |  |
| [EU Social Security Number (SSN) or Equivalent ID](https://learn.microsoft.com/en-us/purview/sit-defn-eu-social-security-number-equivalent-identification) (issue: EU social security number or equivalent identification) | its members | bundle |  |
| [EU Tax Identification Number (TIN)](https://learn.microsoft.com/en-us/purview/sit-defn-eu-tax-identification-number) (issue: EU Tax identification number) | its members | bundle |  |
| [Finland drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-finland-drivers-license-number) | `fi_driver_license` | exact | yes |
| [Finland european health insurance number](https://learn.microsoft.com/en-us/purview/sit-defn-finland-european-health-insurance-number) | `fi_ehic` | exact | yes |
| [Finland national ID](https://learn.microsoft.com/en-us/purview/sit-defn-finland-national-id) | `fi_hetu` | exact |  |
| [Finland passport number](https://learn.microsoft.com/en-us/purview/sit-defn-finland-passport-number) | `fi_passport` | exact | yes |
| [Finland physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-finland-physical-addresses) | `address` | broader |  |
| [France drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-france-drivers-license-number) | `fr_driver_license` | exact | yes |
| [France health insurance number](https://learn.microsoft.com/en-us/purview/sit-defn-france-health-insurance-number) | `fr_health_insurance_number` | exact | yes |
| [France national ID card (CNI)](https://learn.microsoft.com/en-us/purview/sit-defn-france-national-id-card) | `frcni` | exact |  |
| [France passport number](https://learn.microsoft.com/en-us/purview/sit-defn-france-passport-number) | `frpassport` | exact |  |
| [France physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-france-physical-addresses) | `address` | broader |  |
| [France social security number (INSEE)](https://learn.microsoft.com/en-us/purview/sit-defn-france-social-security-number) | `frnir` | exact |  |
| [France Tax Identification Number (numéro SPI.)](https://learn.microsoft.com/en-us/purview/sit-defn-france-tax-identification-number) (issue: France tax identification number) | `fr_nif` | exact |  |
| [France value added tax number](https://learn.microsoft.com/en-us/purview/sit-defn-france-value-added-tax-number) | `frvat` | exact |  |
| [General Password](https://learn.microsoft.com/en-us/purview/sit-defn-general-password) | `password` | exact |  |
| [General Symmetric key](https://learn.microsoft.com/en-us/purview/sit-defn-general-symmetric-key) | `symmetric_key` | exact | yes |
| [Generic medication names](https://learn.microsoft.com/en-us/purview/sit-defn-generic-medication-names) | `medication_generic_name` | exact | yes |
| [German Driver's License Number](https://learn.microsoft.com/en-us/purview/sit-defn-germany-drivers-license-number) (issue: Germany driver's license number) | `dedriverlic` | exact |  |
| [German Passport Number](https://learn.microsoft.com/en-us/purview/sit-defn-germany-passport-number) (issue: Germany passport number) | `de_passport` | exact | yes |
| [Germany identity card number](https://learn.microsoft.com/en-us/purview/sit-defn-germany-identity-card-number) | `depersonalausweis` | exact |  |
| [Germany physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-germany-physical-addresses) | `address` | broader |  |
| [Germany tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-germany-tax-identification-number) | `steuerid` | exact |  |
| [Germany value added tax number](https://learn.microsoft.com/en-us/purview/sit-defn-germany-value-added-tax-number) | `deust` | exact |  |
| [GitHub personal access token](https://learn.microsoft.com/en-us/purview/sit-defn-github-personal-access-token) | `github_token` | exact | yes |
| [Google API key](https://learn.microsoft.com/en-us/purview/sit-defn-google-api-key) | `google_api_key` | exact | yes |
| [Greece drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-greece-drivers-license-number) | `gr_driver_license` | exact | yes |
| [Greece national ID card](https://learn.microsoft.com/en-us/purview/sit-defn-greece-national-id-card) | `gr_id_card` | exact | yes |
| [Greece passport number](https://learn.microsoft.com/en-us/purview/sit-defn-greece-passport-number) | `gr_passport` | exact | yes |
| [Greece physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-greece-physical-addresses) | `address` | broader |  |
| [Greece Social Security Number (AMKA)](https://learn.microsoft.com/en-us/purview/sit-defn-greece-social-security-number) | `gr_amka` | exact |  |
| [Greek Tax Identification Number](https://learn.microsoft.com/en-us/purview/sit-defn-greece-tax-identification-number) (issue: Greece tax identification number) | `gr_vat` | exact |  |
| [Hong Kong identity card (HKID) number](https://learn.microsoft.com/en-us/purview/sit-defn-hong-kong-identity-card-number) | `hk_hkid` | exact | yes |
| [Http authorization header](https://learn.microsoft.com/en-us/purview/sit-defn-http-authorization-header) | `http_authorization_header` | exact | yes |
| [Hungarian Social Security Number (TAJ)](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-social-security-number) (issue: Hungary social security number (TAJ)) | `hu_taj` | exact | yes |
| [Hungarian Value Added Tax Number](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-value-added-tax-number) (issue: Hungary value added tax number) | `hu_anum` | exact |  |
| [Hungary drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-drivers-license-number) | `hu_driver_license` | exact | yes |
| [Hungary passport number](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-passport-number) | `hu_passport` | exact | yes |
| [Hungary personal identification number](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-personal-identification-number) | `hu_personal_id` | exact | yes |
| [Hungary physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-physical-addresses) | `address` | broader |  |
| [Hungary tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-hungary-tax-identification-number) | `hu_tin` | exact | yes |
| [Iceland physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-iceland-physical-addresses) | `address` | broader |  |
| [Impairments Listed In The U.S. Disability Evaluation Under Social Security](https://learn.microsoft.com/en-us/purview/sit-defn-impairments-us-disability-evaluation-under-social-security) | `medical_condition` | broader | yes |
| [India Drivers License Number](https://learn.microsoft.com/en-us/purview/sit-defn-india-drivers-license-number) | `in_driver_license` | exact | yes |
| [India GST Number](https://learn.microsoft.com/en-us/purview/sit-defn-india-gst-number) | `in_gstin` | exact | yes |
| [India permanent account number (PAN)](https://learn.microsoft.com/en-us/purview/sit-defn-india-permanent-account-number) | `pan` | exact |  |
| [India unique identification (Aadhaar) number](https://learn.microsoft.com/en-us/purview/sit-defn-india-unique-identification-number) | `aadhaar` | exact |  |
| [India Voter ID Card](https://learn.microsoft.com/en-us/purview/sit-defn-india-voter-id-card) | `in_epic` | exact | yes |
| [Indonesia identity card (KTP) number](https://learn.microsoft.com/en-us/purview/sit-defn-indonesia-identity-card-number) | `idnik` | exact |  |
| [International banking account number (IBAN)](https://learn.microsoft.com/en-us/purview/sit-defn-international-banking-account-number) | `iban` | exact |  |
| [International classification of diseases (ICD-10-CM)](https://learn.microsoft.com/en-us/purview/sit-defn-international-classification-of-diseases-icd-10-cm) | `icd10`, `medical_condition` | close | yes |
| [International classification of diseases (ICD-9-CM)](https://learn.microsoft.com/en-us/purview/sit-defn-international-classification-of-diseases-icd-9-cm) | `medical_condition` | broader | yes |
| [IP address](https://learn.microsoft.com/en-us/purview/sit-defn-ip-address) | `ipaddr` | exact |  |
| [IP Address v4](https://learn.microsoft.com/en-us/purview/sit-defn-ip-address-v4) | `ipv4` | exact |  |
| [IP Address v6](https://learn.microsoft.com/en-us/purview/sit-defn-ip-address-v6) | `ipv6` | exact |  |
| [Ireland drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-ireland-drivers-license-number) | `ie_driver_license` | exact | yes |
| [Ireland passport number](https://learn.microsoft.com/en-us/purview/sit-defn-ireland-passport-number) | `ie_passport` | exact | yes |
| [Ireland personal public service (PPS) number](https://learn.microsoft.com/en-us/purview/sit-defn-ireland-personal-public-service-number) | `ie_pps` | exact |  |
| [Ireland physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-ireland-physical-addresses) | `address` | broader |  |
| [Israel bank account number](https://learn.microsoft.com/en-us/purview/sit-defn-israel-bank-account-number) | `il_bank_account` | exact | yes |
| [Israel National ID](https://learn.microsoft.com/en-us/purview/sit-defn-israel-national-identification-number) (issue: Israel national identification number) | `il_idnr` | exact |  |
| [Italy drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-italy-drivers-license-number) | `it_driver_license` | exact | yes |
| [Italy fiscal code](https://learn.microsoft.com/en-us/purview/sit-defn-italy-fiscal-code) | `it_codicefiscale` | exact |  |
| [Italy passport number](https://learn.microsoft.com/en-us/purview/sit-defn-italy-passport-number) | `it_passport` | exact | yes |
| [Italy physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-italy-physical-addresses) | `address` | broader |  |
| [Italy value added tax number](https://learn.microsoft.com/en-us/purview/sit-defn-italy-value-added-tax-number) | `it_iva` | exact |  |
| [Japan bank account number](https://learn.microsoft.com/en-us/purview/sit-defn-japan-bank-account-number) | `jp_bank_account` | exact | yes |
| [Japan drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-japan-drivers-license-number) | `jp_driver_license` | exact |  |
| [Japan passport number](https://learn.microsoft.com/en-us/purview/sit-defn-japan-passport-number) | `jp_passport` | exact |  |
| [Japan physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-japan-physical-addresses) | `address` | broader |  |
| [Japan resident registration number](https://learn.microsoft.com/en-us/purview/sit-defn-japan-resident-registration-number) | `jp_resident_registration_number` | exact | yes |
| [Japan social insurance number (SIN)](https://learn.microsoft.com/en-us/purview/sit-defn-japan-social-insurance-number) | `jp_pension_number` | close |  |
| [Japanese My Number Corporate](https://learn.microsoft.com/en-us/purview/sit-defn-japan-my-number-corporate) (issue: Japan My Number - Corporate) | `jp_cn` | exact |  |
| [Japanese My Number Personal](https://learn.microsoft.com/en-us/purview/sit-defn-japan-my-number-personal) (issue: Japan My Number - Personal) | `mynumber` | exact |  |
| [Japanese Residence Card Number](https://learn.microsoft.com/en-us/purview/sit-defn-japan-residence-card-number) (issue: Japan residence card number) | `jp_residence_card` | exact | yes |
| [Lab test terms](https://learn.microsoft.com/en-us/purview/sit-defn-lab-test-terms) | `lab_test` | exact | yes |
| [Latvia drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-latvia-drivers-license-number) | `lv_driver_license` | exact | yes |
| [Latvia passport number](https://learn.microsoft.com/en-us/purview/sit-defn-latvia-passport-number) | `lv_passport` | exact | yes |
| [Latvia personal code](https://learn.microsoft.com/en-us/purview/sit-defn-latvia-personal-code) | `lv_personal_code` | exact | yes |
| [Latvia physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-latvia-physical-addresses) | `address` | broader |  |
| [Liechtenstein physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-liechtenstein-physical-addresses) | `address` | broader |  |
| [Lifestyles that relate to medical conditions](https://learn.microsoft.com/en-us/purview/sit-defn-lifestyles-relate-to-medical-conditions) | - | not linked |  |
| [Lithuania drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-lithuania-drivers-license-number) | `lt_driver_license` | exact | yes |
| [Lithuania passport number](https://learn.microsoft.com/en-us/purview/sit-defn-lithuania-passport-number) | `lt_passport` | exact | yes |
| [Lithuania personal code](https://learn.microsoft.com/en-us/purview/sit-defn-lithuania-personal-code) | `lt_asmens` | exact |  |
| [Lithuania physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-lithuania-physical-addresses) | `address` | broader |  |
| [Luxembourg Driver's License Number](https://learn.microsoft.com/en-us/purview/sit-defn-luxemburg-drivers-license-number) (issue: Luxemburg driver's license number) | `lu_driver_license` | exact | yes |
| [Luxembourg National Identification Number (Natural persons)](https://learn.microsoft.com/en-us/purview/sit-defn-luxemburg-national-identification-number-natural-persons) (issue: Luxemburg national identification number (natural persons)) | `lu_matricule` | exact | yes |
| [Luxembourg National Identification Number (Non-natural persons)](https://learn.microsoft.com/en-us/purview/sit-defn-luxemburg-national-identification-number-non-natural-persons) (issue: Luxemburg national identification number (non-natural persons)) | `lu_matricule_entity` | close | yes |
| [Luxembourg Passport Number](https://learn.microsoft.com/en-us/purview/sit-defn-luxemburg-passport-number) (issue: Luxemburg passport number) | `lu_passport` | exact | yes |
| [Luxembourg Physical Addresses](https://learn.microsoft.com/en-us/purview/sit-defn-luxemburg-physical-addresses) (issue: Luxemburg physical addresses) | `address` | broader |  |
| [Malaysia Identity Card Number](https://learn.microsoft.com/en-us/purview/sit-defn-malaysia-identification-card-number) (issue: Malaysia identification card number) | `my_nric` | exact |  |
| [Malta drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-malta-drivers-license-number) | `mt_driver_license` | exact | yes |
| [Malta identity card number](https://learn.microsoft.com/en-us/purview/sit-defn-malta-identity-card-number) | `mt_id_card` | exact | yes |
| [Malta passport number](https://learn.microsoft.com/en-us/purview/sit-defn-malta-passport-number) | `mt_passport` | exact | yes |
| [Malta physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-malta-physical-addresses) | `address` | broader |  |
| [Malta Tax ID Number](https://learn.microsoft.com/en-us/purview/sit-defn-malta-tax-identification-number) (issue: Malta tax identification number) | `mt_tin` | exact | yes |
| [Medical Specialities](https://learn.microsoft.com/en-us/purview/sit-defn-medical-specialities) | `medical_specialty` | exact | yes |
| [Medicare Beneficiary Identifier (MBI) card](https://learn.microsoft.com/en-us/purview/sit-defn-medicare-beneficiary-identifier-card) | `us_mbi` | exact | yes |
| [Mexico Unique Population Registry Code (CURP)](https://learn.microsoft.com/en-us/purview/sit-defn-mexico-unique-population-registry-code) | `curp` | exact |  |
| [Microsoft Bing maps key](https://learn.microsoft.com/en-us/purview/sit-defn-microsoft-bing-maps-key) | `api_key` | broader | yes |
| [Microsoft Entra client access token](https://learn.microsoft.com/en-us/purview/sit-defn-azure-ad-client-access-token) (issue: Azure AD client access token) | `access_token` | broader | yes |
| [Microsoft Entra client secret](https://learn.microsoft.com/en-us/purview/sit-defn-azure-ad-client-secret) (issue: Azure AD client secret) | `api_key` | broader | yes |
| [Microsoft Entra user credentials](https://learn.microsoft.com/en-us/purview/sit-defn-azure-ad-user-credentials) (issue: Azure AD User Credentials) | `user_credentials` | broader | yes |
| [Netherlands citizens service (BSN) number](https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-citizens-service-number) | `bsn` | exact |  |
| [Netherlands drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-drivers-license-number) | `nl_driver_license` | exact | yes |
| [Netherlands passport number](https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-passport-number) | `nl_passport` | exact | yes |
| [Netherlands physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-physical-addresses) | `address` | broader |  |
| [Netherlands tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-tax-identification-number) | `bsn` | close |  |
| [Netherlands value added tax number](https://learn.microsoft.com/en-us/purview/sit-defn-netherlands-value-added-tax-number) | `nlbtw` | exact |  |
| [New Zealand bank account number](https://learn.microsoft.com/en-us/purview/sit-defn-new-zealand-bank-account-number) | `nz_bankaccount` | exact |  |
| [New Zealand Driver License Number](https://learn.microsoft.com/en-us/purview/sit-defn-new-zealand-drivers-license-number) (issue: New Zealand driver's license number) | `nz_driver_license` | exact | yes |
| [New Zealand inland revenue number](https://learn.microsoft.com/en-us/purview/sit-defn-new-zealand-inland-revenue-number) | `nz_ird` | exact |  |
| [New Zealand ministry of health number](https://learn.microsoft.com/en-us/purview/sit-defn-new-zealand-ministry-of-health-number) | `nz_nhi` | exact | yes |
| [New Zealand physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-new-zealand-physical-addresses) | `address` | broader |  |
| [New Zealand social welfare number](https://learn.microsoft.com/en-us/purview/sit-defn-new-zealand-social-welfare-number) | `nz_swn` | exact | yes |
| [Norway Identity Number](https://learn.microsoft.com/en-us/purview/sit-defn-norway-identification-number) (issue: Norway identification number) | `no_fodselsnummer` | exact |  |
| [Norway physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-norway-physical-addresses) | `address` | broader |  |
| [Philippines passport number](https://learn.microsoft.com/en-us/purview/sit-defn-philippines-passport-number) | `ph_passport` | exact | yes |
| [Philippines Unified Multi-Purpose ID Number](https://learn.microsoft.com/en-us/purview/sit-defn-philippines-unified-multi-purpose-identification-number) (issue: Philippines unified multi-purpose identification number) | `ph_umid` | exact | yes |
| [Poland drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-poland-drivers-license-number) | `pldriverlic` | exact |  |
| [Poland identity card](https://learn.microsoft.com/en-us/purview/sit-defn-poland-identity-card) | `pl_id_card` | exact | yes |
| [Poland national ID (PESEL)](https://learn.microsoft.com/en-us/purview/sit-defn-poland-national-id) | `plpesel` | exact |  |
| [Poland Passport Number](https://learn.microsoft.com/en-us/purview/sit-defn-poland-passport-number) | `plpassport` | exact |  |
| [Poland physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-poland-physical-addresses) | `address` | broader |  |
| [Poland REGON number](https://learn.microsoft.com/en-us/purview/sit-defn-poland-regon-number) | `plregon` | exact |  |
| [Poland tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-poland-tax-identification-number) | `plpesel` | close |  |
| [Portugal citizen card number](https://learn.microsoft.com/en-us/purview/sit-defn-portugal-citizen-card-number) | `pt_cc` | exact | yes |
| [Portugal drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-portugal-drivers-license-number) | `pt_driver_license` | exact | yes |
| [Portugal passport number](https://learn.microsoft.com/en-us/purview/sit-defn-portugal-passport-number) | `pt_passport` | exact | yes |
| [Portugal tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-portugal-tax-identification-number) | `pt_nif` | exact |  |
| [Portuguese physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-portugal-physical-addresses) (issue: Portugal physical addresses) | `address` | broader |  |
| [Qatari ID Card Number](https://learn.microsoft.com/en-us/purview/sit-defn-qatari-id-card-number) (issue: Qatari identification card number) | `qa_qid` | exact | yes |
| [Romania drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-romania-drivers-license-number) | `ro_driver_license` | exact | yes |
| [Romania passport number](https://learn.microsoft.com/en-us/purview/sit-defn-romania-passport-number) | `ro_passport` | exact | yes |
| [Romania personal numeric code (CNP)](https://learn.microsoft.com/en-us/purview/sit-defn-romania-personal-numeric-code) | `ro_cnp` | exact |  |
| [Romania physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-romania-physical-addresses) | `address` | broader |  |
| [Russian Passport Number (Domestic)](https://learn.microsoft.com/en-us/purview/sit-defn-russia-passport-number-domestic) (issue: Russia passport number domestic) | `ruintpassport` | exact |  |
| [Russian Passport Number (International)](https://learn.microsoft.com/en-us/purview/sit-defn-russia-passport-number-international) (issue: Russia passport number international) | `rupassport` | exact |  |
| [Saudi Arabia National ID](https://learn.microsoft.com/en-us/purview/sit-defn-saudi-arabia-national-id) | `said` | exact |  |
| [Singapore national registration identity card (NRIC) number](https://learn.microsoft.com/en-us/purview/sit-defn-singapore-national-registration-identity-card-number) | `sgnric`, `nric` | exact |  |
| [Slack access token](https://learn.microsoft.com/en-us/purview/sit-defn-slack-access-token) | `slack_token` | exact | yes |
| [Slovakia drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-slovakia-drivers-license-number) | `sk_driver_license` | exact | yes |
| [Slovakia passport number](https://learn.microsoft.com/en-us/purview/sit-defn-slovakia-passport-number) | `sk_passport` | exact | yes |
| [Slovakia personal number](https://learn.microsoft.com/en-us/purview/sit-defn-slovakia-personal-number) | `sk_rc` | exact | yes |
| [Slovakia physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-slovakia-physical-addresses) | `address` | broader |  |
| [Slovenia drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-slovenia-drivers-license-number) | `si_driver_license` | exact | yes |
| [Slovenia passport number](https://learn.microsoft.com/en-us/purview/sit-defn-slovenia-passport-number) | `si_passport` | exact | yes |
| [Slovenia physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-slovenia-physical-addresses) | `address` | broader |  |
| [Slovenia tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-slovenia-tax-identification-number) | `si_tin` | exact | yes |
| [Slovenia Unique Master Citizen Number](https://learn.microsoft.com/en-us/purview/sit-defn-slovenia-unique-master-citizen-number) | `si_emso` | exact | yes |
| [South Africa identification number](https://learn.microsoft.com/en-us/purview/sit-defn-south-africa-identification-number) | `za_id` | exact | yes |
| [South Korea resident registration number](https://learn.microsoft.com/en-us/purview/sit-defn-south-korea-resident-registration-number) | `krrrn` | exact |  |
| [Spain DNI](https://learn.microsoft.com/en-us/purview/sit-defn-spain-dni) | `es_dni` | exact |  |
| [Spain drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-spain-drivers-license-number) | `esdriverlic` | exact |  |
| [Spain passport number](https://learn.microsoft.com/en-us/purview/sit-defn-spain-passport-number) | `espassport` | exact |  |
| [Spain physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-spain-physical-addresses) | `address` | broader |  |
| [Spain social security number (SSN)](https://learn.microsoft.com/en-us/purview/sit-defn-spain-social-security-number) | `es_nss` | exact | yes |
| [Spain tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-spain-tax-identification-number) | `esnif` | exact |  |
| [SQL Server connection string](https://learn.microsoft.com/en-us/purview/sit-defn-sql-server-connection-string) | `connection_string` | broader | yes |
| [Surgical procedures](https://learn.microsoft.com/en-us/purview/sit-defn-surgical-procedures) | `surgical_procedure` | exact | yes |
| [Sweden drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-sweden-drivers-license-number) | `se_driver_license` | exact | yes |
| [Sweden national ID](https://learn.microsoft.com/en-us/purview/sit-defn-sweden-national-id) | `sepersonnummer` | exact |  |
| [Sweden passport number](https://learn.microsoft.com/en-us/purview/sit-defn-sweden-passport-number) | `sepassport` | exact |  |
| [Sweden physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-sweden-physical-addresses) | `address` | broader |  |
| [Sweden tax identification number](https://learn.microsoft.com/en-us/purview/sit-defn-sweden-tax-identification-number) | `sepersonnummer` | close |  |
| [SWIFT code](https://learn.microsoft.com/en-us/purview/sit-defn-swift-code) | `swiftcode`, `bic` | exact |  |
| [Swiss Social Security Number AHV](https://learn.microsoft.com/en-us/purview/sit-defn-switzerland-ssn-ahv-number) (issue: Switzerland SSN AHV number) | `chahv` | exact |  |
| [Switzerland physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-switzerland-physical-addresses) | `address` | broader |  |
| [Taiwan National ID](https://learn.microsoft.com/en-us/purview/sit-defn-taiwan-national-identification-number) (issue: Taiwan national identification number) | `tw_national_id` | exact | yes |
| [Taiwan passport number](https://learn.microsoft.com/en-us/purview/sit-defn-taiwan-passport-number) | `tw_passport` | exact | yes |
| [Taiwan Resident Certificate (ARC/TARC)](https://learn.microsoft.com/en-us/purview/sit-defn-taiwan-resident-certificate-number) (issue: Taiwan-resident certificate (ARC/TARC) number) | `tw_arc` | exact | yes |
| [Thai population identification code](https://learn.microsoft.com/en-us/purview/sit-defn-thai-population-identification-code) | `thidcard` | exact |  |
| [Types of medication](https://learn.microsoft.com/en-us/purview/sit-defn-types-of-medication) | `medication_class` | exact | yes |
| [Türkiye national identification number](https://learn.microsoft.com/en-us/purview/sit-defn-turkey-national-identification-number) (issue: Turkey national identification number) | `trtckimlik` | exact |  |
| [Türkiye physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-turkey-physical-addresses) (issue: Turkey physical addresses) | `address` | broader |  |
| [U.K. drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-uk-drivers-license-number) | `ukdriverlic` | exact |  |
| [U.K. electoral roll number](https://learn.microsoft.com/en-us/purview/sit-defn-uk-electoral-roll-number) | `gb_electoral_roll_number` | exact | yes |
| [U.K. national health service number](https://learn.microsoft.com/en-us/purview/sit-defn-uk-national-health-service-number) | `uknhsnum`, `nhsnumber` | exact |  |
| [U.K. national insurance number (NINO)](https://learn.microsoft.com/en-us/purview/sit-defn-uk-national-insurance-number) | `uknino` | exact |  |
| [U.K. physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-uk-physical-addresses) | `address` | broader |  |
| [U.K. Unique Taxpayer Reference Number](https://learn.microsoft.com/en-us/purview/sit-defn-uk-unique-taxpayer-reference-number) | `ukutr` | exact |  |
| [U.S. bank account number](https://learn.microsoft.com/en-us/purview/sit-defn-us-bank-account-number) | `usbankaccount` | exact |  |
| [U.S. drivers license number](https://learn.microsoft.com/en-us/purview/sit-defn-us-drivers-license-number) | `usdriverlic` | exact |  |
| [U.S. individual taxpayer identification number (ITIN)](https://learn.microsoft.com/en-us/purview/sit-defn-us-individual-taxpayer-identification-number) | `usitin` | exact |  |
| [U.S. physical addresses](https://learn.microsoft.com/en-us/purview/sit-defn-us-physical-addresses) | `address` | broader |  |
| [U.S. social security number (SSN)](https://learn.microsoft.com/en-us/purview/sit-defn-us-social-security-number) | `usssn` | exact |  |
| [U.S./U.K. passport number](https://learn.microsoft.com/en-us/purview/sit-defn-us-uk-passport-number) | `uspassport`, `ukpassport` | exact |  |
| [Ukraine Passport Number (Domestic)](https://learn.microsoft.com/en-us/purview/sit-defn-ukraine-passport-domestic) (issue: Ukraine passport domestic) | `ua_passport` | exact | yes |
| [Ukraine Passport Number (International)](https://learn.microsoft.com/en-us/purview/sit-defn-ukraine-passport-international) (issue: Ukraine passport international) | `ua_intpassport` | exact | yes |
| [User login credentials](https://learn.microsoft.com/en-us/purview/sit-defn-user-login-credentials) | `user_credentials` | exact | yes |
| [X.509 certificate private key](https://learn.microsoft.com/en-us/purview/sit-defn-x-509-certificate-private-key) | `x509_private_key` | exact | yes |
