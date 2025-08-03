# **AEC Project Structure & File Naming System**

## **📁 Standard Directory Structure**

PROJECT\_NAME\_PROJECT\_NUMBER/

├── 00\_PROJECT\_MANAGEMENT/

│   ├── Proposals/

│   ├── Contracts/

│   ├── Schedule/

│   ├── Budget/

│   ├── Meeting\_Minutes/

│   ├── Team\_Info/

│   └── Risk\_QA/

├── 01\_CORRESPONDENCE/

│   ├── RFIs/

│   ├── Submittals/

│   ├── Change\_Orders/

│   ├── Transmittals/

│   └── Progress\_Reports/

├── 02\_DRAWINGS/

│   ├── Current/

│   │   ├── Architectural/

│   │   ├── Structural/

│   │   ├── Civil/

│   │   ├── Mechanical/

│   │   ├── Electrical/

│   │   ├── Plumbing/

│   │   └── Specialty/

│   ├── Superseded/

│   ├── Markups/

│   └── Shop\_Drawings/

├── 03\_SPECIFICATIONS/

│   ├── Division\_00\_Bidding/

│   ├── Division\_01\_General/

│   ├── Division\_02\_Site/

│   ├── Division\_03\_Concrete/

│   ├── Division\_04\_Masonry/

│   ├── Division\_05\_Metals/

│   ├── Division\_06\_Wood/

│   ├── Division\_07\_Thermal/

│   ├── Division\_08\_Openings/

│   ├── Division\_09\_Finishes/

│   ├── Division\_10\_Specialties/

│   ├── Division\_11\_Equipment/

│   ├── Division\_12\_Furnishings/

│   ├── Division\_13\_Special/

│   ├── Division\_14\_Conveying/

│   ├── Division\_15\_Mechanical/

│   ├── Division\_16\_Electrical/

│   ├── Division\_31\_Earthwork/

│   ├── Division\_32\_Exterior/

│   ├── Division\_33\_Utilities/

│   └── Master\_Specification/

├── 04\_CALCULATIONS/

│   ├── Structural/

│   ├── Civil/

│   ├── Mechanical/

│   ├── Electrical/

│   └── Other\_Disciplines/

├── 05\_REPORTS/

│   ├── Geotechnical/

│   ├── Environmental/

│   ├── Survey/

│   ├── Testing/

│   └── Studies/

├── 06\_PERMITS\_APPROVALS/

│   ├── Building\_Permits/

│   ├── Zoning/

│   ├── Environmental/

│   ├── Utilities/

│   └── Other\_Agencies/

├── 07\_SITE\_DOCUMENTATION/

│   ├── Photos/

│   ├── Site\_Visits/

│   └── Surveys/

├── 08\_MODELS\_CAD/

│   ├── BIM\_Models/

│   ├── CAD\_Files/

│   ├── 3D\_Models/

│   └── Point\_Clouds/

├── 09\_CONSTRUCTION\_ADMIN/

│   ├── Pre\_Construction/

│   ├── Bidding/

│   ├── Construction\_Phase/

│   └── Completion/

├── 10\_CLOSEOUT/

│   ├── As\_Built\_Drawings/

│   ├── Operations\_Manuals/

│   ├── Warranties/

│   └── Final\_Documentation/

├── 11\_CONSULTANTS/

└── 12\_ARCHIVE/

## **📋 Simplified File Naming Convention**

### **Primary Format**

`Phase_DocumentType_Description_Revision_Date.ext`

### **Phase Codes**

* **PD** \- Pre-Design/Programming  
* **SD** \- Schematic Design  
* **DD** \- Design Development  
* **CD** \- Construction Documents  
* **CA** \- Construction Administration  
* **CO** \- Closeout

  ### **Document Type Codes**

* **DWG** \- Drawings/Plans  
* **CALC** \- Calculations  
* **RPT** \- Reports  
* **SPEC** \- Specifications  
* **RFI** \- Request for Information  
* **SUB** \- Submittal  
* **CHG** \- Change Order  
* **PHO** \- Photos  
* **BIM** \- BIM Models

  ### **Revision System**

**Internal Reviews (Check Prints)**

* C01, C02, C03... \- Internal coordination and review  
* Not issued to external parties

**External Issues (Clean Documents)**

* R0 \- Initial external issue  
* R1, R2, R3... \- Subsequent revisions  
* **IFC** \- Issued for Construction (final)  
* **IFB** \- Issued for Bidding  
* **IFP** \- Issued for Permit

  ## **📝 Naming Examples**

  ### **Drawings**

* `CD_DWG_FloorPlan_Level1_R2_031524.pdf`  
* `DD_DWG_SiteLayout_R1_022824.dwg`  
* `CD_DWG_MechSchedule_R0_041024.pdf`

  ### **Calculations**

* `DD_CALC_StructuralBeams_R2_022024.pdf`  
* `CD_CALC_ElectricalLoads_R1_032524.xlsx`

  ### **Reports**

* `PD_RPT_Geotechnical_R0_011024.pdf`  
* `SD_RPT_Environmental_R1_012524.pdf`

  ### **Specifications**

* `CD_SPEC_Division08_Openings_R1_033024.docx`  
* `CD_SPEC_Division15_HVAC_R2_041224.pdf`

  ### **Correspondence**

* `CA_RFI_001_MechanicalEquipment_R0_052024.pdf`  
* `CA_SUB_SteelFraming_R1_060124.pdf`  
* `CA_CHG_015_SiteWork_R0_061024.pdf`

  ### **Special Formats**

**Meeting Minutes** `MTG_031524_DesignReview.docx`

**Shop Drawings** `SHOP_Steel_AcmeCompany_R1_061524.pdf`

**As-Built Drawings** `AB_FloorPlan_Level1_083024.pdf`

## **🗓️ Date Format**

Always use **MMDDYY** format

## **📎 File Extensions**

* **.pdf** \- Final issued documents  
* **.dwg** \- AutoCAD files  
* **.rvt** \- Revit files  
* **.docx** \- Word documents  
* **.xlsx** \- Excel spreadsheets  
* **.jpg/.png** \- Images


