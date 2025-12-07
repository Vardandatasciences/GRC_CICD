export const iso27001_2013 = {
  version: "2013",
  policies: [
    {
      id: "A.5",
      name: "Information Security Policies",
      description: "Management direction and support for information security",
      changeType: "modified",
      subPolicies: [
        {
          id: "A.5.1",
          name: "Information Security Policy",
          description: "Information security policy document",
          changeType: "modified",
          compliances: [
            {
              id: "A.5.1.1",
              name: "Information Security Policy",
              description: "A set of policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties",
              status: "compliant",
              changeType: "modified"
            },
            {
              id: "A.5.1.2", 
              name: "Review of Information Security Policies",
              description: "Information security policies shall be reviewed at planned intervals or if significant changes occur",
              status: "compliant",
              changeType: "unchanged"
            }
          ]
        }
      ]
    },
    {
      id: "A.6",
      name: "Organization of Information Security",
      description: "Organizational aspects of information security",
      changeType: "modified",
      subPolicies: [
        {
          id: "A.6.1",
          name: "Internal Organization",
          description: "Internal organization of information security",
          changeType: "modified",
          compliances: [
            {
              id: "A.6.1.1",
              name: "Information Security Roles and Responsibilities",
              description: "All information security responsibilities shall be defined and allocated",
              status: "partial",
              changeType: "modified"
            },
            {
              id: "A.6.1.2",
              name: "Segregation of Duties",
              description: "Conflicting duties and areas of responsibility shall be segregated to reduce opportunities for unauthorized or unintentional modification or misuse of the organization's assets",
              status: "non-compliant",
              changeType: "unchanged"
            },
            {
              id: "A.6.1.3",
              name: "Contact with Authorities",
              description: "Appropriate contacts with authorities shall be maintained",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.6.1.4",
              name: "Contact with Special Interest Groups",
              description: "Appropriate contacts with special interest groups or other specialist security forums and professional associations shall be maintained",
              status: "gap",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.6.2",
          name: "Mobile Devices and Teleworking",
          description: "Security of mobile devices and teleworking activities",
          changeType: "removed",
          compliances: [
            {
              id: "A.6.2.1",
              name: "Mobile Device Policy",
              description: "A policy and supporting security measures shall be adopted to manage the risks introduced by using mobile devices",
              status: "gap",
              changeType: "removed"
            },
            {
              id: "A.6.2.2",
              name: "Teleworking",
              description: "A policy and supporting security measures shall be implemented to protect information accessed, processed or stored at teleworking sites",
              status: "non-compliant",
              changeType: "removed"
            }
          ]
        }
      ]
    },
    {
      id: "A.7",
      name: "Human Resource Security",
      description: "Security aspects of human resources",
      changeType: "modified",
      subPolicies: [
        {
          id: "A.7.1",
          name: "Prior to Employment",
          description: "Security measures prior to employment",
          changeType: "modified",
          compliances: [
            {
              id: "A.7.1.1",
              name: "Screening",
              description: "Background verification checks on all candidates for employment shall be carried out in accordance with relevant laws, regulations and ethics and shall be proportional to the business requirements, the classification of the information to be accessed and the perceived risks",
              status: "compliant",
              changeType: "modified"
            },
            {
              id: "A.7.1.2",
              name: "Terms and Conditions of Employment",
              description: "Employment agreements shall state the employee's and the organization's responsibilities for information security",
              status: "partial",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.7.2",
          name: "During Employment",
          description: "Security measures during employment",
          changeType: "modified",
          compliances: [
            {
              id: "A.7.2.1",
              name: "Management Responsibilities",
              description: "Management shall require employees to apply security in accordance with the established policies and procedures of the organization",
              status: "non-compliant",
              changeType: "unchanged"
            },
            {
              id: "A.7.2.2",
              name: "Information Security Awareness, Education and Training",
              description: "All employees of the organization and, where relevant, contractors and third party users shall receive appropriate awareness education and training and regular updates in organizational policies and procedures, as relevant for their job function",
              status: "partial",
              changeType: "modified"
            },
            {
              id: "A.7.2.3",
              name: "Disciplinary Process",
              description: "There shall be a formal and communicated disciplinary process in place to take action against employees who have committed an information security breach",
              status: "compliant",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.7.3",
          name: "Termination and Change of Employment",
          description: "Security measures for termination and change of employment",
          changeType: "unchanged",
          compliances: [
            {
              id: "A.7.3.1",
              name: "Termination Responsibilities",
              description: "Information security responsibilities and duties that remain valid after termination or change of employment shall be defined, communicated to the employee or contractor and enforced",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.7.3.2",
              name: "Return of Assets",
              description: "All employees and external party users shall return all of the organization's assets in their possession upon termination of their employment, contract or agreement",
              status: "partial",
              changeType: "unchanged"
            },
            {
              id: "A.7.3.3",
              name: "Removal of Access Rights",
              description: "All access rights of all employees and external party users to information and information processing facilities shall be removed upon termination of their employment, contract or agreement, or adjusted upon change",
              status: "non-compliant",
              changeType: "unchanged"
            }
          ]
        }
      ]
    },
    {
      id: "A.8",
      name: "Asset Management",
      description: "Achieve and maintain appropriate protection of organizational assets",
      changeType: "modified",
      subPolicies: [
        {
          id: "A.8.1",
          name: "Responsibility for Assets",
          description: "Identification of organizational assets",
          changeType: "modified",
          compliances: [
            {
              id: "A.8.1.1",
              name: "Inventory of Assets",
              description: "Assets associated with information and information processing facilities shall be identified and an inventory of these assets shall be drawn up and maintained",
              status: "partial",
              changeType: "modified"
            },
            {
              id: "A.8.1.2",
              name: "Ownership of Assets",
              description: "Assets maintained in the inventory shall be owned and the ownership shall be clearly defined and assigned",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.8.1.3",
              name: "Acceptable Use of Assets",
              description: "Rules for the acceptable use of information and of assets associated with information and information processing facilities shall be identified, documented and implemented",
              status: "partial",
              changeType: "unchanged"
            },
            {
              id: "A.8.1.4",
              name: "Return of Assets",
              description: "All employees and external party users shall return all of the organization's assets in their possession upon termination of their employment, contract or agreement",
              status: "compliant",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.8.2",
          name: "Information Classification",
          description: "Classification of information",
          changeType: "unchanged",
          compliances: [
            {
              id: "A.8.2.1",
              name: "Classification of Information",
              description: "Information shall be classified in terms of legal requirements, value, criticality and sensitivity to unauthorized disclosure or modification",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.8.2.2",
              name: "Labeling of Information",
              description: "An appropriate set of procedures for information labeling shall be developed and implemented in accordance with the information classification scheme adopted by the organization",
              status: "partial",
              changeType: "unchanged"
            },
            {
              id: "A.8.2.3",
              name: "Handling of Assets",
              description: "Procedures for handling assets shall be developed and implemented in accordance with the information classification scheme adopted by the organization",
              status: "non-compliant",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.8.3",
          name: "Media Handling",
          description: "Handling of media",
          changeType: "unchanged",
          compliances: [
            {
              id: "A.8.3.1",
              name: "Management of Removable Media",
              description: "Procedures shall be implemented for the management of removable media in accordance with the classification scheme adopted by the organization",
              status: "gap",
              changeType: "unchanged"
            },
            {
              id: "A.8.3.2",
              name: "Disposal of Media",
              description: "Media shall be disposed of securely when no longer required, using formal procedures",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.8.3.3",
              name: "Physical Media Transfer",
              description: "Media containing information shall be protected against unauthorized access, misuse or corruption during transportation",
              status: "partial",
              changeType: "unchanged"
            }
          ]
        }
      ]
    },
    {
      id: "A.9",
      name: "Access Control",
      description: "Limit access to information and information processing facilities",
      changeType: "modified",
      subPolicies: [
        {
          id: "A.9.1",
          name: "Business Requirements of Access Control",
          description: "Access control policy and procedures",
          changeType: "modified",
          compliances: [
            {
              id: "A.9.1.1",
              name: "Access Control Policy",
              description: "An access control policy shall be established, documented and reviewed based on business and information security requirements",
              status: "compliant",
              changeType: "modified"
            },
            {
              id: "A.9.1.2",
              name: "Access to Networks and Network Services",
              description: "Users shall only be provided with access to the network and network services that they have been specifically authorized to use",
              status: "non-compliant",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.9.2",
          name: "User Access Management",
          description: "User access management",
          changeType: "modified",
          compliances: [
            {
              id: "A.9.2.1",
              name: "User Registration and De-registration",
              description: "A formal user registration and de-registration process shall be implemented to enable assignment of access rights",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.9.2.2",
              name: "User Access Provisioning",
              description: "A formal user access provisioning process shall be implemented to assign or revoke access rights for all user types to all systems and services",
              status: "partial",
              changeType: "modified"
            },
            {
              id: "A.9.2.3",
              name: "Access Rights Management",
              description: "The allocation and use of privileged access rights shall be restricted and controlled",
              status: "non-compliant",
              changeType: "modified"
            },
            {
              id: "A.9.2.4",
              name: "Review of User Access Rights",
              description: "Asset owners shall review users' access rights at regular intervals using a formal process",
              status: "gap",
              changeType: "unchanged"
            },
            {
              id: "A.9.2.5",
              name: "Removal or Adjustment of Access Rights",
              description: "The access rights of all employees and external party users to information and information processing facilities shall be removed upon termination of their employment, contract or agreement, or adjusted upon change",
              status: "partial",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.9.3",
          name: "User Responsibilities",
          description: "User responsibilities",
          changeType: "unchanged",
          compliances: [
            {
              id: "A.9.3.1",
              name: "Use of Secret Authentication Information",
              description: "Users shall be required to follow the organization's practices in the use of secret authentication information",
              status: "compliant",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.9.4",
          name: "System and Application Access Control",
          description: "System and application access control",
          changeType: "modified",
          compliances: [
            {
              id: "A.9.4.1",
              name: "Information Access Restriction",
              description: "Access to information and application system functions shall be restricted in accordance with the defined access control policy",
              status: "non-compliant",
              changeType: "modified"
            },
            {
              id: "A.9.4.2",
              name: "Secure Log-on Procedures",
              description: "Where required by the access control policy, access to systems and applications shall be controlled by a secure log-on procedure",
              status: "compliant",
              changeType: "unchanged"
            },
            {
              id: "A.9.4.3",
              name: "Password Management System",
              description: "Password management systems shall be interactive and shall ensure quality passwords",
              status: "partial",
              changeType: "unchanged"
            },
            {
              id: "A.9.4.4",
              name: "Use of Privileged Utility Programs",
              description: "The use of utility programs that might be capable of overriding system and application controls shall be restricted and tightly controlled",
              status: "gap",
              changeType: "unchanged"
            },
            {
              id: "A.9.4.5",
              name: "Access Control to Program Source Code",
              description: "Access to program source code shall be restricted",
              status: "compliant",
              changeType: "unchanged"
            }
          ]
        }
      ]
    }
  ]
};

export const iso27001_2022 = {
  version: "2022",
  policies: [
    {
      id: "A.5",
      name: "Organizational Controls",
      description: "Controls related to organizational aspects of information security",
      changeType: "modified",
      subPolicies: [
        {
          id: "A.5.1",
          name: "Information Security Policies",
          description: "Information security policy and topic-specific policies",
          changeType: "modified",
          compliances: [
            {
              id: "A.5.1.1",
              name: "Information Security Policy",
              description: "An information security policy shall be defined, approved by management, published and communicated to employees and relevant external parties",
              status: "compliant",
              changeType: "modified"
            },
            {
              id: "A.5.1.2",
              name: "Information Security Policy Review",
              description: "Information security policies shall be reviewed at planned intervals or if significant changes occur",
              status: "compliant",
              changeType: "unchanged"
            }
          ]
        },
        {
          id: "A.5.2",
          name: "Information Security Roles and Responsibilities",
          description: "Information security roles and responsibilities",
          changeType: "new",
          compliances: [
            {
              id: "A.5.2.1",
              name: "Information Security Roles and Responsibilities",
              description: "Information security roles and responsibilities shall be defined and allocated in accordance with the organization's needs",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.3",
          name: "Segregation of Duties",
          description: "Segregation of duties to reduce opportunities for unauthorized modification",
          changeType: "new",
          compliances: [
            {
              id: "A.5.3.1",
              name: "Segregation of Duties",
              description: "Conflicting duties and areas of responsibility shall be segregated to reduce opportunities for unauthorized or unintentional modification or misuse of the organization's assets",
              status: "non-compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.4",
          name: "Management Responsibilities",
          description: "Management responsibilities for information security",
          changeType: "new",
          compliances: [
            {
              id: "A.5.4.1",
              name: "Management Responsibilities",
              description: "Management shall require employees to apply security in accordance with the established policies and procedures of the organization",
              status: "non-compliant",
              changeType: "new"
        }
      ]
    },
    {
          id: "A.5.5",
          name: "Contact with Authorities",
          description: "Contact with authorities",
          changeType: "new",
          compliances: [
            {
              id: "A.5.5.1",
              name: "Contact with Authorities",
              description: "Appropriate contacts with authorities shall be maintained",
              status: "compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.6",
          name: "Contact with Special Interest Groups",
          description: "Contact with special interest groups",
          changeType: "new",
          compliances: [
            {
              id: "A.5.6.1",
              name: "Contact with Special Interest Groups",
              description: "Appropriate contacts with special interest groups or other specialist security forums and professional associations shall be maintained",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.7",
          name: "Threat Intelligence",
          description: "Threat intelligence and information security threat assessment",
          changeType: "new",
          compliances: [
            {
              id: "A.5.7.1",
              name: "Threat Intelligence",
              description: "Information relating to information security threats shall be collected and analyzed to produce threat intelligence",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.8",
          name: "Information Security in Project Management",
          description: "Information security in project management",
          changeType: "new",
          compliances: [
            {
              id: "A.5.8.1",
              name: "Information Security in Project Management",
              description: "Information security shall be addressed in project management, regardless of the type of the project",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.9",
          name: "Inventory of Information and Other Associated Assets",
          description: "Inventory of information and other associated assets",
          changeType: "new",
          compliances: [
            {
              id: "A.5.9.1",
              name: "Inventory of Information and Other Associated Assets",
              description: "Assets associated with information and information processing facilities shall be identified and an inventory of these assets shall be drawn up and maintained",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.10",
          name: "Acceptable Use of Information and Other Associated Assets",
          description: "Acceptable use of information and other associated assets",
          changeType: "new",
          compliances: [
            {
              id: "A.5.10.1",
              name: "Acceptable Use of Information and Other Associated Assets",
              description: "Rules for the acceptable use of information and of assets associated with information and information processing facilities shall be identified, documented and implemented",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.11",
          name: "Return of Assets",
          description: "Return of assets",
          changeType: "new",
          compliances: [
            {
              id: "A.5.11.1",
              name: "Return of Assets",
              description: "All employees and external party users shall return all of the organization's assets in their possession upon termination of their employment, contract or agreement",
              status: "compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.12",
          name: "Classification of Information",
          description: "Classification of information",
          changeType: "new",
          compliances: [
            {
              id: "A.5.12.1",
              name: "Classification of Information",
              description: "Information shall be classified in terms of legal requirements, value, criticality and sensitivity to unauthorized disclosure or modification",
              status: "compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.13",
          name: "Labelling of Information",
          description: "Labelling of information",
          changeType: "new",
          compliances: [
            {
              id: "A.5.13.1",
              name: "Labelling of Information",
              description: "An appropriate set of procedures for information labelling shall be developed and implemented in accordance with the information classification scheme adopted by the organization",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.14",
          name: "Information Transfer",
          description: "Information transfer",
          changeType: "new",
          compliances: [
            {
              id: "A.5.14.1",
              name: "Information Transfer",
              description: "Procedures shall be implemented for the management of removable media in accordance with the classification scheme adopted by the organization",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.15",
          name: "Access Control",
          description: "Access control",
          changeType: "new",
          compliances: [
            {
              id: "A.5.15.1",
              name: "Access Control",
              description: "An access control policy shall be established, documented and reviewed based on business and information security requirements",
              status: "compliant",
              changeType: "new"
        }
      ]
    },
    {
          id: "A.5.16",
          name: "Identity Verification",
          description: "Identity verification",
          changeType: "new",
          compliances: [
            {
              id: "A.5.16.1",
              name: "Identity Verification",
              description: "A formal user registration and de-registration process shall be implemented to enable assignment of access rights",
              status: "compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.17",
          name: "Access Rights and Access Management",
          description: "Access rights and access management",
          changeType: "new",
          compliances: [
            {
              id: "A.5.17.1",
              name: "Access Rights and Access Management",
              description: "A formal user access provisioning process shall be implemented to assign or revoke access rights for all user types to all systems and services",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.18",
          name: "Information Security in Supplier Relationships",
          description: "Information security in supplier relationships",
          changeType: "new",
          compliances: [
            {
              id: "A.5.18.1",
              name: "Information Security in Supplier Relationships",
              description: "Information security requirements for mitigating the risks associated with supplier's access to the organization's assets shall be agreed with the supplier and documented",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.19",
          name: "ICT Supply Chain Security",
          description: "ICT supply chain security",
          changeType: "new",
          compliances: [
            {
              id: "A.5.19.1",
              name: "ICT Supply Chain Security",
              description: "Agreements with suppliers shall include requirements to address the information security risks associated with information and communications technology services and product supply chain",
              status: "gap",
              changeType: "new"
        }
      ]
    },
    {
          id: "A.5.20",
          name: "Monitoring, Review and Change Management of Supplier Services",
          description: "Monitoring, review and change management of supplier services",
          changeType: "new",
          compliances: [
            {
              id: "A.5.20.1",
              name: "Monitoring, Review and Change Management of Supplier Services",
              description: "Organizations shall regularly monitor, review and audit supplier service delivery",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.21",
          name: "Information Security for Use of Cloud Services",
          description: "Information security for use of cloud services",
          changeType: "new",
          compliances: [
            {
              id: "A.5.21.1",
              name: "Information Security for Use of Cloud Services",
              description: "Processes for acquisition, use, management and exit from cloud services shall be established in accordance with the organization's information security requirements",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.22",
          name: "Information Security Incident Management",
          description: "Information security incident management",
          changeType: "new",
          compliances: [
            {
              id: "A.5.22.1",
              name: "Information Security Incident Management",
              description: "Information security events shall be assessed and it shall be decided if they are to be classified as information security incidents",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.23",
          name: "Information Security Incident Management Process",
          description: "Information security incident management process",
          changeType: "new",
          compliances: [
            {
              id: "A.5.23.1",
              name: "Information Security Incident Management Process",
              description: "A consistent and effective approach shall be applied to the management of information security incidents",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.24",
          name: "Incident Reporting",
          description: "Incident reporting",
          changeType: "new",
          compliances: [
            {
              id: "A.5.24.1",
              name: "Incident Reporting",
              description: "Information security events shall be reported through appropriate management channels as quickly as possible",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.25",
          name: "Incident Learning",
          description: "Incident learning",
          changeType: "new",
          compliances: [
            {
              id: "A.5.25.1",
              name: "Incident Learning",
              description: "Knowledge gained from analyzing and resolving information security incidents shall be used to reduce the likelihood or impact of future incidents",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.26",
          name: "Collection of Evidence",
          description: "Collection of evidence",
          changeType: "new",
          compliances: [
            {
              id: "A.5.26.1",
              name: "Collection of Evidence",
              description: "The organization shall define and apply procedures for the identification, collection, acquisition and preservation of information, which can serve as evidence",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.27",
          name: "Information Security During Disruption",
          description: "Information security during disruption",
          changeType: "new",
          compliances: [
            {
              id: "A.5.27.1",
              name: "Information Security During Disruption",
              description: "The organization shall plan how to maintain information security at an appropriate level during disruption",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.28",
          name: "ICT Readiness for Business Continuity",
          description: "ICT readiness for business continuity",
          changeType: "new",
          compliances: [
            {
              id: "A.5.28.1",
              name: "ICT Readiness for Business Continuity",
              description: "ICT continuity plans shall be developed, maintained and tested based on business continuity objectives and ICT continuity requirements",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.29",
          name: "Legal, Statutory, Regulatory and Contractual Requirements",
          description: "Legal, statutory, regulatory and contractual requirements",
          changeType: "new",
          compliances: [
            {
              id: "A.5.29.1",
              name: "Legal, Statutory, Regulatory and Contractual Requirements",
              description: "All relevant legislative, statutory, regulatory, contractual requirements and the organization's approach to meet these requirements shall be explicitly identified, documented and kept up to date for each information system and the organization",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.30",
          name: "Protection of Records",
          description: "Protection of records",
          changeType: "new",
          compliances: [
            {
              id: "A.5.30.1",
              name: "Protection of Records",
              description: "Records shall be protected from loss, destruction, falsification, unauthorized access and unauthorized release, in accordance with legislative, statutory, regulatory, contractual and business requirements",
              status: "compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.31",
          name: "Privacy and Protection of PII",
          description: "Privacy and protection of PII",
          changeType: "new",
          compliances: [
            {
              id: "A.5.31.1",
              name: "Privacy and Protection of PII",
              description: "Privacy and protection of personally identifiable information (PII) shall be ensured as required in relevant legislation and regulation where applicable",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.32",
          name: "Protection of Information in Cloud Services",
          description: "Protection of information in cloud services",
          changeType: "new",
          compliances: [
            {
              id: "A.5.32.1",
              name: "Protection of Information in Cloud Services",
              description: "The organization shall determine and implement appropriate controls for the protection of information in cloud services",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.33",
          name: "Independent Review of Information Security",
          description: "Independent review of information security",
          changeType: "new",
          compliances: [
            {
              id: "A.5.33.1",
              name: "Independent Review of Information Security",
              description: "The organization's approach to managing information security and its implementation (i.e. control objectives, controls, policies, processes and procedures for information security) shall be reviewed independently at planned intervals or when significant changes occur",
              status: "gap",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.34",
          name: "Compliance with Policies, Rules and Standards",
          description: "Compliance with policies, rules and standards",
          changeType: "new",
          compliances: [
            {
              id: "A.5.34.1",
              name: "Compliance with Policies, Rules and Standards",
              description: "Managers shall regularly review the compliance of information processing and procedures within their area of responsibility with the appropriate policies, rules and standards",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.35",
          name: "Documented Operating Procedures",
          description: "Documented operating procedures",
          changeType: "new",
          compliances: [
            {
              id: "A.5.35.1",
              name: "Documented Operating Procedures",
              description: "Operating procedures shall be documented and made available to all users who need them",
              status: "compliant",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.36",
          name: "Change Management",
          description: "Change management",
          changeType: "new",
          compliances: [
            {
              id: "A.5.36.1",
              name: "Change Management",
              description: "Changes to information processing facilities and systems shall be controlled",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.37",
          name: "Capacity Management",
          description: "Capacity management",
          changeType: "new",
          compliances: [
            {
              id: "A.5.37.1",
              name: "Capacity Management",
              description: "The use of resources shall be monitored, tuned and projections made of future capacity requirements to ensure the required system performance",
              status: "partial",
              changeType: "new"
            }
          ]
        },
        {
          id: "A.5.38",
          name: "Separation of Development, Test and Production Environments",
          description: "Separation of development, test and production environments",
          changeType: "new",
          compliances: [
            {
              id: "A.5.38.1",
              name: "Separation of Development, Test and Production Environments",
              description: "Development, test and production environments shall be separated and managed",
              status: "compliant",
              changeType: "new"
            }
          ]
        }
      ]
    }
  ]
};

export const migrationSummary = {
  totalNonCompliances2013: 12,
  newRequirements2022: 38,
  modifiedCompliances: 8,
  overallProgress: 0
};

export const actionPlan = [
  {
    policy: "A.5.2.1",
    requirement: "Information Security Roles and Responsibilities",
    currentStatus: "gap",
    action: "Define and document information security roles and responsibilities",
    priority: "High",
    effort: "2-3 weeks",
    owner: "CISO"
  },
  {
    policy: "A.5.3.1", 
    requirement: "Segregation of Duties",
    currentStatus: "non-compliant",
    action: "Review and update segregation of duties matrix",
    priority: "High",
    effort: "1-2 weeks",
    owner: "HR Manager"
  },
  {
    policy: "A.5.4.1",
    requirement: "Management Responsibilities",
    currentStatus: "non-compliant",
    action: "Establish management oversight and accountability framework",
    priority: "High",
    effort: "2-4 weeks",
    owner: "Senior Management"
  },
  {
    policy: "A.5.6.1",
    requirement: "Contact with Special Interest Groups",
    currentStatus: "gap",
    action: "Establish relationships with security forums and professional associations",
    priority: "Medium",
    effort: "3-4 weeks",
    owner: "CISO"
  },
  {
    policy: "A.5.7.1",
    requirement: "Threat Intelligence",
    currentStatus: "gap",
    action: "Implement threat intelligence collection and analysis capabilities",
    priority: "High",
    effort: "6-8 weeks",
    owner: "Security Team"
  },
  {
    policy: "A.5.8.1",
    requirement: "Information Security in Project Management",
    currentStatus: "gap",
    action: "Integrate security requirements into project management methodology",
    priority: "Medium",
    effort: "4-6 weeks",
    owner: "PMO"
  },
  {
    policy: "A.5.9.1",
    requirement: "Inventory of Information and Other Associated Assets",
    currentStatus: "partial",
    action: "Complete asset inventory and establish maintenance procedures",
    priority: "Medium",
    effort: "3-4 weeks",
    owner: "IT Manager"
  },
  {
    policy: "A.5.10.1",
    requirement: "Acceptable Use of Information and Other Associated Assets",
    currentStatus: "partial",
    action: "Update acceptable use policies and procedures",
    priority: "Medium",
    effort: "2-3 weeks",
    owner: "Legal Team"
  },
  {
    policy: "A.5.12.1",
    requirement: "Classification of Information",
    currentStatus: "compliant",
    action: "Review and update information classification scheme",
    priority: "Low",
    effort: "1-2 weeks",
    owner: "Data Protection Officer"
  },
  {
    policy: "A.5.13.1",
    requirement: "Labelling of Information",
    currentStatus: "partial",
    action: "Implement information labeling procedures",
    priority: "Medium",
    effort: "3-4 weeks",
    owner: "IT Manager"
  },
  {
    policy: "A.5.14.1",
    requirement: "Information Transfer",
    currentStatus: "gap",
    action: "Establish secure information transfer procedures",
    priority: "High",
    effort: "4-5 weeks",
    owner: "Security Team"
  },
  {
    policy: "A.5.15.1",
    requirement: "Access Control",
    currentStatus: "compliant",
    action: "Review and update access control policies",
    priority: "Low",
    effort: "1-2 weeks",
    owner: "IT Security Manager"
  },
  {
    policy: "A.5.16.1",
    requirement: "Identity Verification",
    currentStatus: "compliant",
    action: "Enhance user registration and de-registration processes",
    priority: "Low",
    effort: "1-2 weeks",
    owner: "IT Manager"
  },
  {
    policy: "A.5.17.1",
    requirement: "Access Rights and Access Management",
    currentStatus: "partial",
    action: "Implement formal access provisioning and revocation processes",
    priority: "High",
    effort: "4-6 weeks",
    owner: "IT Security Manager"
  },
  {
    policy: "A.5.18.1",
    requirement: "Information Security in Supplier Relationships",
    currentStatus: "gap",
    action: "Establish supplier security requirements and agreements",
    priority: "High",
    effort: "6-8 weeks",
    owner: "Procurement Manager"
  },
  {
    policy: "A.5.19.1",
    requirement: "ICT Supply Chain Security",
    currentStatus: "gap",
    action: "Implement ICT supply chain security controls",
    priority: "High",
    effort: "8-10 weeks",
    owner: "Procurement Manager"
  },
  {
    policy: "A.5.20.1",
    requirement: "Monitoring, Review and Change Management of Supplier Services",
    currentStatus: "gap",
    action: "Establish supplier service monitoring and review processes",
    priority: "Medium",
    effort: "4-5 weeks",
    owner: "Vendor Management"
  },
  {
    policy: "A.5.21.1",
    requirement: "Information Security for Use of Cloud Services",
    currentStatus: "gap",
    action: "Develop cloud service security framework",
    priority: "High",
    effort: "8-12 weeks",
    owner: "Cloud Security Team"
  },
  {
    policy: "A.5.22.1",
    requirement: "Information Security Incident Management",
    currentStatus: "partial",
    action: "Enhance incident detection and assessment capabilities",
    priority: "High",
    effort: "4-6 weeks",
    owner: "Security Operations"
  },
  {
    policy: "A.5.23.1",
    requirement: "Information Security Incident Management Process",
    currentStatus: "gap",
    action: "Establish comprehensive incident management process",
    priority: "High",
    effort: "6-8 weeks",
    owner: "Security Operations"
  },
  {
    policy: "A.5.24.1",
    requirement: "Incident Reporting",
    currentStatus: "partial",
    action: "Implement incident reporting procedures and channels",
    priority: "Medium",
    effort: "3-4 weeks",
    owner: "Security Operations"
  },
  {
    policy: "A.5.25.1",
    requirement: "Incident Learning",
    currentStatus: "gap",
    action: "Establish incident learning and improvement processes",
    priority: "Medium",
    effort: "4-5 weeks",
    owner: "Security Operations"
  },
  {
    policy: "A.5.26.1",
    requirement: "Collection of Evidence",
    currentStatus: "gap",
    action: "Implement evidence collection and preservation procedures",
    priority: "Medium",
    effort: "4-6 weeks",
    owner: "Legal Team"
  },
  {
    policy: "A.5.27.1",
    requirement: "Information Security During Disruption",
    currentStatus: "gap",
    action: "Develop business continuity security procedures",
    priority: "High",
    effort: "6-8 weeks",
    owner: "Business Continuity Manager"
  },
  {
    policy: "A.5.28.1",
    requirement: "ICT Readiness for Business Continuity",
    currentStatus: "gap",
    action: "Establish ICT continuity planning and testing",
    priority: "High",
    effort: "8-10 weeks",
    owner: "IT Manager"
  },
  {
    policy: "A.5.29.1",
    requirement: "Legal, Statutory, Regulatory and Contractual Requirements",
    currentStatus: "partial",
    action: "Conduct comprehensive compliance assessment",
    priority: "High",
    effort: "6-8 weeks",
    owner: "Compliance Officer"
  },
  {
    policy: "A.5.30.1",
    requirement: "Protection of Records",
    currentStatus: "compliant",
    action: "Review and update records protection procedures",
    priority: "Low",
    effort: "1-2 weeks",
    owner: "Records Manager"
  },
  {
    policy: "A.5.31.1",
    requirement: "Privacy and Protection of PII",
    currentStatus: "gap",
    action: "Implement PII protection controls and procedures",
    priority: "High",
    effort: "6-8 weeks",
    owner: "Data Protection Officer"
  },
  {
    policy: "A.5.32.1",
    requirement: "Protection of Information in Cloud Services",
    currentStatus: "gap",
    action: "Implement cloud information protection controls",
    priority: "High",
    effort: "8-10 weeks",
    owner: "Cloud Security Team"
  },
  {
    policy: "A.5.33.1",
    requirement: "Independent Review of Information Security",
    currentStatus: "gap",
    action: "Establish independent security review program",
    priority: "Medium",
    effort: "4-6 weeks",
    owner: "Internal Audit"
  },
  {
    policy: "A.5.34.1",
    requirement: "Compliance with Policies, Rules and Standards",
    currentStatus: "partial",
    action: "Implement compliance monitoring and review processes",
    priority: "Medium",
    effort: "4-5 weeks",
    owner: "Compliance Officer"
  },
  {
    policy: "A.5.35.1",
    requirement: "Documented Operating Procedures",
    currentStatus: "compliant",
    action: "Review and update operating procedures",
    priority: "Low",
    effort: "1-2 weeks",
    owner: "Operations Manager"
  },
  {
    policy: "A.5.36.1",
    requirement: "Change Management",
    currentStatus: "partial",
    action: "Enhance change management processes",
    priority: "Medium",
    effort: "3-4 weeks",
    owner: "Change Manager"
  },
  {
    policy: "A.5.37.1",
    requirement: "Capacity Management",
    currentStatus: "partial",
    action: "Implement capacity monitoring and planning",
    priority: "Medium",
    effort: "4-5 weeks",
    owner: "IT Manager"
  },
  {
    policy: "A.5.38.1",
    requirement: "Separation of Development, Test and Production Environments",
    currentStatus: "compliant",
    action: "Review environment separation controls",
    priority: "Low",
    effort: "1-2 weeks",
    owner: "DevOps Manager"
  }
];
