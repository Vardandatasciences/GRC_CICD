// Framework-specific content configuration
export const frameworkContent = {
  // Basel III Framework
  'basel3': {
    frameworkName: 'Basel 3',
    hero: {
      badge: 'GRC Compliance Platform',
      title: ['Enterprise GRC', ' Platform', ' with Basel 3 Excellence'],
      description: 'Achieve comprehensive compliance with our integrated platform covering Financial Risk Management (Basel 3) framework. Drive regulatory alignment and risk management excellence with automated monitoring and expert guidance.',
      stats: [
        { number: '76%', label: 'Basel 3 Compliance' },
        { number: '4', label: 'Months Implementation' },
        { number: '7', label: 'Basel 3 Policies' },
        { number: '22', label: 'Total Controls' }
      ],
      previewMetrics: [
        {
          title: 'Capital Adequacy',
          value: '78%',
          change: '+8%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Liquidity Coverage',
          value: '82%',
          change: '+5%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Risk Management',
          value: '76%',
          change: '+12%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'Basel 3 Implementation Progress',
        percentage: '76%',
        implementationTime: '4 months',
        remainingControls: '24% (Basel 3)',
        nextAudit: 'Q3 2024',
        policiesLabel: 'Basel 3 Policies',
        policiesValue: '7 Total'
      }
    },
    compliance: {
      title: 'Your Basel 3 Compliance Journey',
      description: 'Track your progress through Basel 3 framework with real-time monitoring, automated assessments, and expert guidance. Currently at 85% overall compliance.',
      features: [
        {
          title: 'Automated Basel 3 Assessment',
          description: 'AI-powered assessment of Basel 3 financial risk controls with real-time compliance scoring and gap analysis.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Risk Monitoring',
          description: '24/7 monitoring of financial risk indicators, capital adequacy ratios, and compliance metrics with automated alerts.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Comprehensive Risk Assessment',
          description: 'Detailed financial risk assessment with stress testing, scenario analysis, and mitigation planning.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'Regulatory Reporting',
          description: 'Automated generation of Basel 3 compliance reports for regulators, auditors, and stakeholders with customizable dashboards.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Capital Adequacy Policy',
        description: 'Establish processes to assess and maintain adequate capital levels for risk coverage as per Basel 3 requirements.',
        compliance: 80,
        controls: 5,
        implemented: 4,
        remaining: 1,
        status: 'completed',
        framework: 'Basel 3'
      },
      {
        title: 'Liquidity Risk Management Policy',
        description: 'Implement liquidity coverage and net stable funding ratios as per Basel 3 framework.',
        compliance: 83,
        controls: 6,
        implemented: 5,
        remaining: 1,
        status: 'completed',
        framework: 'Basel 3'
      },
      {
        title: 'Leverage Ratio Policy',
        description: 'Maintain leverage ratio requirements to limit excessive leverage and ensure financial stability.',
        compliance: 75,
        controls: 4,
        implemented: 3,
        remaining: 1,
        status: 'completed',
        framework: 'Basel 3'
      },
      {
        title: 'Risk Disclosure & Transparency Policy',
        description: 'Ensure comprehensive risk disclosure and transparency in financial reporting and regulatory submissions.',
        compliance: 71,
        controls: 7,
        implemented: 5,
        remaining: 2,
        status: 'completed',
        framework: 'Basel 3'
      },
      {
        title: 'Stress Testing & Risk Management Policy',
        description: 'Conduct regular stress testing and implement comprehensive risk management frameworks.',
        compliance: 67,
        controls: 3,
        implemented: 2,
        remaining: 1,
        status: 'in-progress',
        framework: 'Basel 3'
      },
      {
        title: 'Counterparty Credit Risk Policy',
        description: 'Manage counterparty credit risk using standardized approaches and internal models.',
        compliance: 0,
        controls: 2,
        implemented: 0,
        remaining: 2,
        status: 'draft',
        framework: 'Basel 3'
      }
    ],
    benefits: [
      {
        title: 'Accelerated Basel 3 Implementation',
        description: 'Achieve comprehensive Basel 3 compliance in 6-10 months with our proven methodology and automated tools.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Enhanced Risk Management',
        description: 'Real-time monitoring of financial risk metrics, capital adequacy ratios, and compliance KPIs with automated alerts.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert Basel 3 Guidance',
        description: 'Access to financial risk experts with deep knowledge of Basel 3 regulatory requirements and banking best practices.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Comprehensive Basel 3 Reporting',
        description: 'Detailed compliance dashboards and regulatory reports with audit-ready evidence for regulators and stakeholders.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve Basel 3 Compliance?',
      description: 'Join hundreds of organizations that have successfully implemented Basel 3 framework with our platform. Start your compliance journey today and achieve 85% compliance within 6 months.',
      primaryButton: 'Start Basel 3 Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Capital Adequacy Policy', status: 'Approved', version: '2.1', created_date: '2013-01-01', framework: 'Basel 3' },
          { id: 2, name: 'Liquidity Risk Management Policy', status: 'Approved', version: '2.0', created_date: '2013-01-01', framework: 'Basel 3' },
          { id: 3, name: 'Leverage Ratio Policy', status: 'Approved', version: '1.9', created_date: '2013-01-01', framework: 'Basel 3' },
          { id: 4, name: 'Risk Disclosure & Transparency Policy', status: 'Approved', version: '1.8', created_date: '2013-01-01', framework: 'Basel 3' }
        ], 
        count: 4, 
        percentage: 67 
      },
      in_progress: { 
        policies: [
          { id: 5, name: 'Stress Testing & Risk Management Policy', status: 'Under Review', version: '0.9', created_date: '2013-01-01', framework: 'Basel 3' }
        ], 
        count: 1, 
        percentage: 17 
      },
      pending: { 
        policies: [
          { id: 6, name: 'Counterparty Credit Risk Policy', status: 'Draft', version: '0.7', created_date: '2013-01-01', framework: 'Basel 3' }
        ], 
        count: 1, 
        percentage: 16 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'Capital Adequacy Ratio (CAR)',
          value: '12.5%',
          label: 'Current CAR',
          status: 'pass',
          description: 'Minimum requirement: 10.5%',
          trend: 'up',
          change: '+1.2%'
        },
        {
          title: 'Common Equity Tier 1 (CET1)',
          value: '10.8%',
          label: 'CET1 Ratio',
          status: 'monitor',
          description: 'Minimum requirement: 7%',
          trend: 'stable',
          change: '+0.3%'
        },
        {
          title: 'Liquidity Coverage Ratio (LCR)',
          value: '125%',
          label: 'Current LCR',
          status: 'pass',
          description: 'Minimum requirement: 100%',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Net Stable Funding Ratio (NSFR)',
          value: '115%',
          label: 'Current NSFR',
          status: 'pass',
          description: 'Minimum requirement: 100%',
          trend: 'up',
          change: '+5%'
        },
        {
          title: 'Leverage Ratio',
          value: '5.2%',
          label: 'Current Leverage',
          status: 'pass',
          description: 'Minimum requirement: 3%',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Risk-Weighted Assets (RWA)',
          value: '€245B',
          label: 'Total RWA',
          status: 'monitor',
          description: 'Year-over-year comparison',
          trend: 'up',
          change: '+12%'
        }
      ],
      showBaselKPIs: true
    }
  },

  // ISO 27001:2022 Framework
  'iso27001': {
    frameworkName: 'ISO 27001:2022',
    hero: {
      badge: 'Information Security Platform',
      title: ['Enterprise Security', ' Management', ' with ISO 27001:2022'],
      description: 'Achieve comprehensive information security management with our integrated platform covering ISO 27001:2022 framework. Drive security excellence and risk management with automated monitoring and expert guidance.',
      stats: [
        { number: '89%', label: 'ISO 27001 Compliance' },
        { number: '6', label: 'Months Implementation' },
        { number: '12', label: 'Security Policies' },
        { number: '93', label: 'Security Controls' }
      ],
      previewMetrics: [
        {
          title: 'Information Security',
          value: '92%',
          change: '+15%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Access Control',
          value: '88%',
          change: '+10%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Incident Response',
          value: '85%',
          change: '+8%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'ISO 27001:2022 Implementation Progress',
        percentage: '89%',
        implementationTime: '6 months',
        remainingControls: '11% (ISO 27001)',
        nextAudit: 'Q4 2024',
        policiesLabel: 'Security Policies',
        policiesValue: '12 Total'
      }
    },
    compliance: {
      title: 'Your ISO 27001:2022 Compliance Journey',
      description: 'Track your progress through ISO 27001:2022 framework with real-time monitoring, automated assessments, and expert guidance. Currently at 89% overall compliance.',
      features: [
        {
          title: 'Automated Security Assessment',
          description: 'AI-powered assessment of ISO 27001:2022 security controls with real-time compliance scoring and gap analysis.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Continuous Monitoring',
          description: '24/7 monitoring of security controls, incidents, and compliance metrics with automated alerts and notifications.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Risk Assessment',
          description: 'Comprehensive information security risk assessment with threat analysis and treatment planning.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'Audit Management',
          description: 'Streamlined audit preparation with evidence collection, documentation, and certification readiness reports.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Information Security Policies',
        description: 'Define and maintain comprehensive information security policies aligned with ISO 27001:2022 requirements.',
        compliance: 95,
        controls: 8,
        implemented: 8,
        remaining: 0,
        status: 'completed',
        framework: 'ISO 27001:2022'
      },
      {
        title: 'Access Control Management',
        description: 'Implement robust access control mechanisms to protect information assets and ensure appropriate access.',
        compliance: 88,
        controls: 14,
        implemented: 12,
        remaining: 2,
        status: 'completed',
        framework: 'ISO 27001:2022'
      },
      {
        title: 'Cryptography & Key Management',
        description: 'Establish cryptographic controls and key management processes to protect sensitive information.',
        compliance: 82,
        controls: 6,
        implemented: 5,
        remaining: 1,
        status: 'completed',
        framework: 'ISO 27001:2022'
      },
      {
        title: 'Security Operations',
        description: 'Implement operational security controls for system and network security management.',
        compliance: 90,
        controls: 18,
        implemented: 16,
        remaining: 2,
        status: 'completed',
        framework: 'ISO 27001:2022'
      },
      {
        title: 'Incident Management',
        description: 'Establish and maintain information security incident management processes and procedures.',
        compliance: 85,
        controls: 7,
        implemented: 6,
        remaining: 1,
        status: 'in-progress',
        framework: 'ISO 27001:2022'
      },
      {
        title: 'Business Continuity',
        description: 'Ensure business continuity and disaster recovery planning for critical information systems.',
        compliance: 78,
        controls: 5,
        implemented: 4,
        remaining: 1,
        status: 'in-progress',
        framework: 'ISO 27001:2022'
      }
    ],
    benefits: [
      {
        title: 'Accelerated ISO 27001 Certification',
        description: 'Achieve ISO 27001:2022 certification in 6-12 months with our proven methodology and compliance automation.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Enhanced Information Security',
        description: 'Comprehensive security controls and continuous monitoring to protect your organization\'s information assets.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert Security Guidance',
        description: 'Access to ISO 27001 certified consultants and security experts for implementation and audit support.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Audit-Ready Documentation',
        description: 'Automated evidence collection and documentation management for seamless certification audits.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve ISO 27001:2022 Certification?',
      description: 'Join thousands of organizations worldwide that have achieved ISO 27001:2022 certification with our platform. Start your information security journey today.',
      primaryButton: 'Start ISO 27001 Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Information Security Policy', status: 'Approved', version: '3.2', created_date: '2022-01-15', framework: 'ISO 27001:2022' },
          { id: 2, name: 'Access Control Policy', status: 'Approved', version: '2.8', created_date: '2022-02-01', framework: 'ISO 27001:2022' },
          { id: 3, name: 'Cryptography Policy', status: 'Approved', version: '2.1', created_date: '2022-02-15', framework: 'ISO 27001:2022' },
          { id: 4, name: 'Physical Security Policy', status: 'Approved', version: '1.9', created_date: '2022-03-01', framework: 'ISO 27001:2022' },
          { id: 5, name: 'Operations Security Policy', status: 'Approved', version: '2.5', created_date: '2022-03-15', framework: 'ISO 27001:2022' },
          { id: 6, name: 'Communications Security Policy', status: 'Approved', version: '1.7', created_date: '2022-04-01', framework: 'ISO 27001:2022' },
          { id: 7, name: 'Asset Management Policy', status: 'Approved', version: '2.0', created_date: '2022-04-15', framework: 'ISO 27001:2022' },
          { id: 8, name: 'Human Resource Security Policy', status: 'Approved', version: '1.8', created_date: '2022-05-01', framework: 'ISO 27001:2022' }
        ], 
        count: 8, 
        percentage: 67 
      },
      in_progress: { 
        policies: [
          { id: 9, name: 'Incident Management Policy', status: 'Under Review', version: '1.5', created_date: '2022-05-15', framework: 'ISO 27001:2022' },
          { id: 10, name: 'Business Continuity Policy', status: 'Under Review', version: '1.3', created_date: '2022-06-01', framework: 'ISO 27001:2022' }
        ], 
        count: 2, 
        percentage: 17 
      },
      pending: { 
        policies: [
          { id: 11, name: 'Supplier Relationship Policy', status: 'Draft', version: '0.8', created_date: '2022-06-15', framework: 'ISO 27001:2022' },
          { id: 12, name: 'Compliance & Audit Policy', status: 'Draft', version: '0.6', created_date: '2022-07-01', framework: 'ISO 27001:2022' }
        ], 
        count: 2, 
        percentage: 16 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'Security Control Implementation',
          value: '89%',
          label: 'Controls Implemented',
          status: 'pass',
          description: '93 controls: 83 implemented, 10 in progress',
          trend: 'up',
          change: '+12%'
        },
        {
          title: 'Security Incidents',
          value: '5',
          label: 'Monthly Incidents',
          status: 'pass',
          description: 'Average response time: 2.3 hours',
          trend: 'down',
          change: '-18%'
        },
        {
          title: 'Vulnerability Management',
          value: '94%',
          label: 'Remediation Rate',
          status: 'pass',
          description: 'Critical: 100%, High: 95%, Medium: 88%',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Access Control Compliance',
          value: '96%',
          label: 'User Access Reviews',
          status: 'pass',
          description: 'Quarterly reviews: 96% completion',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Security Awareness Training',
          value: '92%',
          label: 'Completion Rate',
          status: 'pass',
          description: 'Annual training: 550/600 employees',
          trend: 'up',
          change: '+5%'
        },
        {
          title: 'Risk Assessment Coverage',
          value: '88%',
          label: 'Assets Assessed',
          status: 'monitor',
          description: '156/178 critical assets assessed',
          trend: 'up',
          change: '+15%'
        },
        {
          title: 'Audit Findings',
          value: '12',
          label: 'Open Findings',
          status: 'monitor',
          description: 'High: 2, Medium: 6, Low: 4',
          trend: 'down',
          change: '-25%'
        },
        {
          title: 'Encryption Coverage',
          value: '100%',
          label: 'Data at Rest',
          status: 'pass',
          description: 'All sensitive data encrypted',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Backup Success Rate',
          value: '99.8%',
          label: 'Monthly Average',
          status: 'pass',
          description: 'Last failed backup: 15 days ago',
          trend: 'up',
          change: '+0.3%'
        },
        {
          title: 'Patch Management',
          value: '91%',
          label: 'Systems Up-to-Date',
          status: 'pass',
          description: 'Critical patches: 98%, Security: 94%',
          trend: 'up',
          change: '+7%'
        }
      ]
    }
  },

  // NIST 800-53 Framework
  'nist80053': {
    frameworkName: 'NIST 800-53',
    hero: {
      badge: 'Federal Security Compliance',
      title: ['Enterprise Security', ' Framework', ' with NIST 800-53'],
      description: 'Achieve comprehensive federal security compliance with our integrated platform covering NIST 800-53 framework. Drive security excellence for federal systems and contractors.',
      stats: [
        { number: '82%', label: 'NIST 800-53 Compliance' },
        { number: '8', label: 'Months Implementation' },
        { number: '18', label: 'Security Policies' },
        { number: '325', label: 'Security Controls' }
      ],
      previewMetrics: [
        {
          title: 'Access Control',
          value: '85%',
          change: '+12%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Audit & Accountability',
          value: '88%',
          change: '+7%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Security Assessment',
          value: '80%',
          change: '+10%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'NIST 800-53 Implementation Progress',
        percentage: '82%',
        implementationTime: '8 months',
        remainingControls: '18% (NIST 800-53)',
        nextAudit: 'Q1 2025',
        policiesLabel: 'Security Policies',
        policiesValue: '18 Total'
      }
    },
    compliance: {
      title: 'Your NIST 800-53 Compliance Journey',
      description: 'Track your progress through NIST 800-53 framework with real-time monitoring, automated assessments, and expert guidance. Currently at 82% overall compliance.',
      features: [
        {
          title: 'Automated Control Assessment',
          description: 'AI-powered assessment of NIST 800-53 security controls with real-time compliance scoring and continuous monitoring.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Continuous Authorization',
          description: 'Support for continuous ATO (Authority to Operate) with automated evidence collection and real-time risk assessment.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Control Tailoring',
          description: 'Flexible control tailoring and overlay management for system-specific security requirements.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'FedRAMP Support',
          description: 'Complete FedRAMP authorization support with automated SSP generation and compliance tracking.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Access Control (AC)',
        description: 'Implement comprehensive access control policies and procedures to limit system access to authorized users.',
        compliance: 85,
        controls: 25,
        implemented: 21,
        remaining: 4,
        status: 'completed',
        framework: 'NIST 800-53'
      },
      {
        title: 'Audit and Accountability (AU)',
        description: 'Establish audit logging and accountability mechanisms for all system activities and events.',
        compliance: 88,
        controls: 16,
        implemented: 14,
        remaining: 2,
        status: 'completed',
        framework: 'NIST 800-53'
      },
      {
        title: 'Security Assessment (CA)',
        description: 'Conduct regular security assessments and continuous monitoring of security controls.',
        compliance: 80,
        controls: 9,
        implemented: 7,
        remaining: 2,
        status: 'completed',
        framework: 'NIST 800-53'
      },
      {
        title: 'Configuration Management (CM)',
        description: 'Establish and maintain baseline configurations and change control processes.',
        compliance: 78,
        controls: 14,
        implemented: 11,
        remaining: 3,
        status: 'in-progress',
        framework: 'NIST 800-53'
      },
      {
        title: 'Incident Response (IR)',
        description: 'Develop and implement incident response capabilities for security incidents.',
        compliance: 82,
        controls: 10,
        implemented: 8,
        remaining: 2,
        status: 'in-progress',
        framework: 'NIST 800-53'
      },
      {
        title: 'System and Communications Protection (SC)',
        description: 'Protect system boundaries and communications through network security controls.',
        compliance: 75,
        controls: 51,
        implemented: 38,
        remaining: 13,
        status: 'in-progress',
        framework: 'NIST 800-53'
      }
    ],
    benefits: [
      {
        title: 'Accelerated ATO Process',
        description: 'Achieve Authority to Operate (ATO) faster with automated evidence collection and continuous monitoring.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Federal Compliance',
        description: 'Meet federal security requirements with comprehensive NIST 800-53 control implementation and monitoring.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert Federal Guidance',
        description: 'Access to federal security experts with deep knowledge of NIST, FedRAMP, and federal compliance requirements.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Continuous Authorization',
        description: 'Support for continuous ATO with automated monitoring and real-time compliance reporting.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve NIST 800-53 Compliance?',
      description: 'Join federal agencies and contractors that have achieved NIST 800-53 compliance and FedRAMP authorization with our platform.',
      primaryButton: 'Start NIST 800-53 Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Access Control Policy (AC)', status: 'Approved', version: '2.5', created_date: '2023-01-10', framework: 'NIST 800-53' },
          { id: 2, name: 'Audit and Accountability Policy (AU)', status: 'Approved', version: '2.3', created_date: '2023-01-20', framework: 'NIST 800-53' },
          { id: 3, name: 'Security Assessment Policy (CA)', status: 'Approved', version: '2.1', created_date: '2023-02-01', framework: 'NIST 800-53' },
          { id: 4, name: 'Configuration Management Policy (CM)', status: 'Approved', version: '1.9', created_date: '2023-02-15', framework: 'NIST 800-53' },
          { id: 5, name: 'Identification and Authentication Policy (IA)', status: 'Approved', version: '2.4', created_date: '2023-03-01', framework: 'NIST 800-53' },
          { id: 6, name: 'System and Communications Protection Policy (SC)', status: 'Approved', version: '2.2', created_date: '2023-03-15', framework: 'NIST 800-53' },
          { id: 7, name: 'System and Information Integrity Policy (SI)', status: 'Approved', version: '1.8', created_date: '2023-04-01', framework: 'NIST 800-53' }
        ], 
        count: 7, 
        percentage: 61 
      },
      in_progress: { 
        policies: [
          { id: 8, name: 'Incident Response Policy (IR)', status: 'Under Review', version: '1.5', created_date: '2023-04-15', framework: 'NIST 800-53' },
          { id: 9, name: 'Contingency Planning Policy (CP)', status: 'Under Review', version: '1.4', created_date: '2023-05-01', framework: 'NIST 800-53' },
          { id: 10, name: 'Media Protection Policy (MP)', status: 'Under Review', version: '1.2', created_date: '2023-05-15', framework: 'NIST 800-53' }
        ], 
        count: 3, 
        percentage: 26 
      },
      pending: { 
        policies: [
          { id: 11, name: 'Physical and Environmental Protection Policy (PE)', status: 'Draft', version: '0.9', created_date: '2023-06-01', framework: 'NIST 800-53' },
          { id: 12, name: 'Risk Assessment Policy (RA)', status: 'Draft', version: '0.7', created_date: '2023-06-15', framework: 'NIST 800-53' }
        ], 
        count: 2, 
        percentage: 13 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'Control Implementation Status',
          value: '82%',
          label: 'Controls Implemented',
          status: 'monitor',
          description: '325 controls: 267 implemented, 58 in progress',
          trend: 'up',
          change: '+10%'
        },
        {
          title: 'Authorization to Operate (ATO)',
          value: 'Active',
          label: 'Current Status',
          status: 'pass',
          description: 'Valid until: December 2025',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Continuous Monitoring',
          value: '95%',
          label: 'Monitoring Coverage',
          status: 'pass',
          description: 'Real-time monitoring of 312/325 controls',
          trend: 'up',
          change: '+5%'
        },
        {
          title: 'POA&M Items',
          value: '23',
          label: 'Open Items',
          status: 'monitor',
          description: 'High: 5, Medium: 12, Low: 6',
          trend: 'down',
          change: '-15%'
        },
        {
          title: 'Security Scans',
          value: '98.5%',
          label: 'Compliance Rate',
          status: 'pass',
          description: 'Weekly scans: 142/144 passed',
          trend: 'up',
          change: '+2%'
        },
        {
          title: 'Configuration Compliance',
          value: '91%',
          label: 'Baseline Adherence',
          status: 'pass',
          description: 'USGCB/DISA STIG compliance',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Access Control Reviews',
          value: '96%',
          label: 'Quarterly Completion',
          status: 'pass',
          description: 'Privileged accounts: 100% reviewed',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Incident Response Time',
          value: '1.8h',
          label: 'Mean Time',
          status: 'pass',
          description: 'Target: < 2 hours',
          trend: 'down',
          change: '-15%'
        },
        {
          title: 'Evidence Collection',
          value: '89%',
          label: 'Automated',
          status: 'monitor',
          description: '285/325 controls automated',
          trend: 'up',
          change: '+12%'
        },
        {
          title: 'Audit Readiness',
          value: '94%',
          label: 'Ready for Assessment',
          status: 'pass',
          description: '306/325 controls audit-ready',
          trend: 'up',
          change: '+7%'
        }
      ]
    }
  },

  // PCI DSS Framework
  'pcidss': {
    frameworkName: 'PCI DSS',
    hero: {
      badge: 'Payment Security Platform',
      title: ['Payment Card', ' Data Security', ' with PCI DSS Excellence'],
      description: 'Achieve comprehensive payment card data security with our integrated platform covering PCI DSS framework. Protect cardholder data and ensure compliance with payment card industry standards.',
      stats: [
        { number: '91%', label: 'PCI DSS Compliance' },
        { number: '5', label: 'Months Implementation' },
        { number: '15', label: 'Security Policies' },
        { number: '12', label: 'Control Domains' }
      ],
      previewMetrics: [
        {
          title: 'Network Security',
          value: '94%',
          change: '+18%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Data Protection',
          value: '92%',
          change: '+12%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Access Control',
          value: '89%',
          change: '+10%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'PCI DSS Implementation Progress',
        percentage: '91%',
        implementationTime: '5 months',
        remainingControls: '9% (PCI DSS)',
        nextAudit: 'Q2 2025',
        policiesLabel: 'PCI DSS Policies',
        policiesValue: '15 Total'
      }
    },
    compliance: {
      title: 'Your PCI DSS Compliance Journey',
      description: 'Track your progress through PCI DSS framework with real-time monitoring, automated assessments, and expert guidance. Currently at 91% overall compliance.',
      features: [
        {
          title: 'Automated PCI Assessment',
          description: 'AI-powered assessment of PCI DSS requirements with real-time compliance scoring and vulnerability detection.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Cardholder Data Monitoring',
          description: '24/7 monitoring of cardholder data environment (CDE) with automated alerts for security events.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Vulnerability Management',
          description: 'Continuous vulnerability scanning and penetration testing for PCI DSS compliance requirements.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'QSA-Ready Reports',
          description: 'Automated SAQ and ROC preparation with complete evidence collection for QSA validation.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Build and Maintain Secure Network',
        description: 'Install and maintain firewall configuration to protect cardholder data environments.',
        compliance: 95,
        controls: 7,
        implemented: 7,
        remaining: 0,
        status: 'completed',
        framework: 'PCI DSS'
      },
      {
        title: 'Protect Cardholder Data',
        description: 'Protect stored cardholder data with encryption and ensure secure transmission over networks.',
        compliance: 92,
        controls: 8,
        implemented: 7,
        remaining: 1,
        status: 'completed',
        framework: 'PCI DSS'
      },
      {
        title: 'Vulnerability Management Program',
        description: 'Maintain vulnerability management program with regular scanning and system updates.',
        compliance: 88,
        controls: 6,
        implemented: 5,
        remaining: 1,
        status: 'completed',
        framework: 'PCI DSS'
      },
      {
        title: 'Strong Access Control Measures',
        description: 'Restrict access to cardholder data by business need-to-know and implement strong authentication.',
        compliance: 90,
        controls: 9,
        implemented: 8,
        remaining: 1,
        status: 'completed',
        framework: 'PCI DSS'
      },
      {
        title: 'Monitor and Test Networks',
        description: 'Track and monitor all access to network resources and cardholder data.',
        compliance: 85,
        controls: 11,
        implemented: 9,
        remaining: 2,
        status: 'in-progress',
        framework: 'PCI DSS'
      },
      {
        title: 'Information Security Policy',
        description: 'Maintain policy that addresses information security for all personnel.',
        compliance: 93,
        controls: 9,
        implemented: 8,
        remaining: 1,
        status: 'completed',
        framework: 'PCI DSS'
      }
    ],
    benefits: [
      {
        title: 'Accelerated PCI Compliance',
        description: 'Achieve PCI DSS compliance and validation in 4-8 months with automated assessment and monitoring.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Payment Data Protection',
        description: 'Comprehensive protection of cardholder data with encryption, tokenization, and access controls.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert PCI Guidance',
        description: 'Access to PCI QSAs and payment security experts for compliance and validation support.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Continuous Compliance',
        description: 'Maintain continuous PCI DSS compliance with automated monitoring and quarterly reporting.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve PCI DSS Compliance?',
      description: 'Join thousands of merchants and service providers that have achieved PCI DSS compliance with our platform. Protect your cardholder data today.',
      primaryButton: 'Start PCI DSS Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Firewall and Router Configuration Policy', status: 'Approved', version: '4.2', created_date: '2021-06-01', framework: 'PCI DSS' },
          { id: 2, name: 'Vendor-Supplied Defaults Policy', status: 'Approved', version: '3.8', created_date: '2021-06-15', framework: 'PCI DSS' },
          { id: 3, name: 'Cardholder Data Protection Policy', status: 'Approved', version: '4.5', created_date: '2021-07-01', framework: 'PCI DSS' },
          { id: 4, name: 'Data Transmission Encryption Policy', status: 'Approved', version: '3.9', created_date: '2021-07-15', framework: 'PCI DSS' },
          { id: 5, name: 'Anti-Malware Policy', status: 'Approved', version: '3.6', created_date: '2021-08-01', framework: 'PCI DSS' },
          { id: 6, name: 'Secure Systems and Applications Policy', status: 'Approved', version: '3.4', created_date: '2021-08-15', framework: 'PCI DSS' },
          { id: 7, name: 'Access Control Policy', status: 'Approved', version: '4.1', created_date: '2021-09-01', framework: 'PCI DSS' },
          { id: 8, name: 'Authentication Policy', status: 'Approved', version: '3.7', created_date: '2021-09-15', framework: 'PCI DSS' },
          { id: 9, name: 'Physical Access Policy', status: 'Approved', version: '3.5', created_date: '2021-10-01', framework: 'PCI DSS' },
          { id: 10, name: 'Network Activity Monitoring Policy', status: 'Approved', version: '4.0', created_date: '2021-10-15', framework: 'PCI DSS' }
        ], 
        count: 10, 
        percentage: 67 
      },
      in_progress: { 
        policies: [
          { id: 11, name: 'Security Testing Policy', status: 'Under Review', version: '2.8', created_date: '2021-11-01', framework: 'PCI DSS' },
          { id: 12, name: 'Vulnerability Management Policy', status: 'Under Review', version: '2.6', created_date: '2021-11-15', framework: 'PCI DSS' }
        ], 
        count: 2, 
        percentage: 13 
      },
      pending: { 
        policies: [
          { id: 13, name: 'Information Security Policy', status: 'Draft', version: '1.9', created_date: '2021-12-01', framework: 'PCI DSS' },
          { id: 14, name: 'Incident Response Policy', status: 'Draft', version: '1.7', created_date: '2021-12-15', framework: 'PCI DSS' },
          { id: 15, name: 'Third-Party Service Provider Policy', status: 'Draft', version: '1.5', created_date: '2022-01-01', framework: 'PCI DSS' }
        ], 
        count: 3, 
        percentage: 20 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'PCI DSS Compliance Score',
          value: '91%',
          label: 'Overall Compliance',
          status: 'pass',
          description: 'All 12 requirements assessed',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Cardholder Data Environment (CDE)',
          value: '100%',
          label: 'Network Segmentation',
          status: 'pass',
          description: 'CDE properly isolated and monitored',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Vulnerability Scans',
          value: '0',
          label: 'Critical Vulnerabilities',
          status: 'pass',
          description: 'Last scan: 5 days ago (Quarterly)',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Penetration Testing',
          value: 'Pass',
          label: 'Annual Test',
          status: 'pass',
          description: 'Last test: 3 months ago',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'File Integrity Monitoring',
          value: '99.2%',
          label: 'Monitoring Coverage',
          status: 'pass',
          description: 'All critical files monitored',
          trend: 'up',
          change: '+1%'
        },
        {
          title: 'Encryption Status',
          value: '100%',
          label: 'Data Protection',
          status: 'pass',
          description: 'All cardholder data encrypted',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Access Control',
          value: '98%',
          label: 'Least Privilege',
          status: 'pass',
          description: 'Role-based access implemented',
          trend: 'up',
          change: '+3%'
        },
        {
          title: 'Audit Log Review',
          value: '100%',
          label: 'Daily Review',
          status: 'pass',
          description: 'All logs reviewed and archived',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Anti-Malware Updates',
          value: '100%',
          label: 'Up-to-Date',
          status: 'pass',
          description: 'Real-time protection active',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Vendor Compliance',
          value: '95%',
          label: 'Third-Party Validation',
          status: 'pass',
          description: '38/40 vendors PCI compliant',
          trend: 'up',
          change: '+5%'
        }
      ]
    }
  },

  // FDA Framework
  'fda': {
    frameworkName: 'Food and Drug Administration',
    hero: {
      badge: 'FDA Compliance Platform',
      title: ['FDA Regulatory', ' Compliance', ' Platform'],
      description: 'Achieve comprehensive FDA compliance with our integrated platform covering food, drug, and medical device regulations. Drive regulatory alignment and product safety excellence with automated monitoring.',
      stats: [
        { number: '91%', label: 'FDA Compliance' },
        { number: '12', label: 'Months Implementation' },
        { number: '18', label: 'FDA Policies' },
        { number: '92', label: 'Total Controls' }
      ],
      previewMetrics: [
        {
          title: 'Regulatory Compliance',
          value: '95%',
          change: '+18%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Quality Assurance',
          value: '89%',
          change: '+12%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Document Control',
          value: '87%',
          change: '+15%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'FDA Implementation Progress',
        percentage: '91%',
        implementationTime: '12 months',
        remainingControls: '9% (FDA)',
        nextAudit: 'Q2 2025',
        policiesLabel: 'FDA Policies',
        policiesValue: '18 Total'
      }
    },
    compliance: {
      title: 'Your FDA Compliance Journey',
      description: 'Track your progress through FDA regulations with real-time monitoring, automated assessments, and expert guidance. Currently at 91% overall compliance.',
      features: [
        {
          title: 'FDA Regulatory Assessment',
          description: 'AI-powered assessment of FDA regulatory requirements with real-time compliance scoring and gap analysis.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Quality System Monitoring',
          description: '24/7 monitoring of GMP compliance, quality metrics, and regulatory requirements with automated alerts.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Document Management',
          description: 'Comprehensive regulatory document control with version management and approval workflows.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'FDA Reporting',
          description: 'Automated generation of FDA submissions, adverse event reports, and regulatory compliance documentation.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Good Manufacturing Practice (GMP)',
        description: 'Establish and maintain GMP compliance for pharmaceutical and food manufacturing processes.',
        compliance: 94,
        controls: 15,
        implemented: 14,
        remaining: 1,
        status: 'completed',
        framework: 'FDA'
      },
      {
        title: 'Quality System Regulation (QSR)',
        description: 'Implement quality system regulations for medical devices with design controls and validation.',
        compliance: 91,
        controls: 18,
        implemented: 16,
        remaining: 2,
        status: 'completed',
        framework: 'FDA'
      },
      {
        title: 'Hazard Analysis Critical Control Points (HACCP)',
        description: 'Develop and implement HACCP plans for food safety and hazard prevention.',
        compliance: 88,
        controls: 12,
        implemented: 10,
        remaining: 2,
        status: 'completed',
        framework: 'FDA'
      },
      {
        title: 'Adverse Event Reporting',
        description: 'Establish processes for timely and accurate adverse event reporting to FDA.',
        compliance: 85,
        controls: 14,
        implemented: 12,
        remaining: 2,
        status: 'in-progress',
        framework: 'FDA'
      },
      {
        title: 'Document Control and Recordkeeping',
        description: 'Maintain comprehensive document control systems for regulatory compliance and audits.',
        compliance: 92,
        controls: 16,
        implemented: 14,
        remaining: 2,
        status: 'completed',
        framework: 'FDA'
      },
      {
        title: 'Labeling and Advertising Compliance',
        description: 'Ensure accurate product labeling and advertising compliance with FDA regulations.',
        compliance: 87,
        controls: 11,
        implemented: 9,
        remaining: 2,
        status: 'completed',
        framework: 'FDA'
      }
    ],
    benefits: [
      {
        title: 'Accelerated FDA Approval',
        description: 'Achieve FDA approval faster with automated compliance monitoring and comprehensive regulatory support.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Regulatory Excellence',
        description: 'Comprehensive FDA compliance coverage for food, drugs, medical devices, and biologics.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert FDA Guidance',
        description: 'Access to FDA regulatory experts with deep knowledge of pharmaceutical and medical device regulations.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Regulatory Documentation',
        description: 'Automated FDA submission preparation and regulatory compliance documentation.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve FDA Compliance?',
      description: 'Join leading pharmaceutical and food companies that have achieved FDA compliance with our platform. Start your regulatory compliance journey today.',
      primaryButton: 'Start FDA Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Good Manufacturing Practice Policy', status: 'Approved', version: '3.2', created_date: '2021-01-10', framework: 'FDA' },
          { id: 2, name: 'Quality System Regulation Policy', status: 'Approved', version: '2.8', created_date: '2021-02-01', framework: 'FDA' },
          { id: 3, name: 'HACCP Policy', status: 'Approved', version: '2.5', created_date: '2021-03-01', framework: 'FDA' },
          { id: 4, name: 'Adverse Event Reporting Policy', status: 'Approved', version: '2.3', created_date: '2021-04-01', framework: 'FDA' },
          { id: 5, name: 'Document Control Policy', status: 'Approved', version: '2.1', created_date: '2021-05-01', framework: 'FDA' }
        ], 
        count: 5, 
        percentage: 63 
      },
      in_progress: { 
        policies: [
          { id: 6, name: 'Labeling Compliance Policy', status: 'Under Review', version: '1.8', created_date: '2021-06-01', framework: 'FDA' },
          { id: 7, name: 'Clinical Trial Management Policy', status: 'Under Review', version: '1.6', created_date: '2021-07-01', framework: 'FDA' }
        ], 
        count: 2, 
        percentage: 25 
      },
      pending: { 
        policies: [
          { id: 8, name: 'Risk Management Policy', status: 'Draft', version: '0.9', created_date: '2021-08-01', framework: 'FDA' }
        ], 
        count: 1, 
        percentage: 12 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'FDA Compliance Score',
          value: '91%',
          label: 'Overall Compliance',
          status: 'pass',
          description: 'GMP, QSR, and HACCP compliance',
          trend: 'up',
          change: '+14%'
        },
        {
          title: 'GMP Audit Findings',
          value: '2',
          label: 'Open Findings',
          status: 'pass',
          description: 'Down from 5 last quarter',
          trend: 'down',
          change: '-60%'
        },
        {
          title: 'Adverse Event Reports',
          value: '8',
          label: 'Monthly Average',
          status: 'pass',
          description: 'All reports submitted within 18h',
          trend: 'up',
          change: '+6%'
        },
        {
          title: 'Document Control',
          value: '97%',
          label: 'Version Compliance',
          status: 'pass',
          description: 'All documents current',
          trend: 'up',
          change: '+4%'
        },
        {
          title: 'Quality Assurance',
          value: '96%',
          label: 'Pass Rate',
          status: 'pass',
          description: 'Product quality testing',
          trend: 'up',
          change: '+5%'
        },
        {
          title: 'FDA Inspections',
          value: 'Pass',
          label: 'Last Inspection',
          status: 'pass',
          description: 'No 483s issued',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Batch Release',
          value: '94%',
          label: 'On-Time Release',
          status: 'pass',
          description: 'Within 36 hours',
          trend: 'up',
          change: '+6%'
        },
        {
          title: 'Corrective Actions',
          value: '65',
          label: 'Closed This Quarter',
          status: 'pass',
          description: 'CAPA effectiveness',
          trend: 'up',
          change: '+18%'
        },
        {
          title: 'Training Compliance',
          value: '95%',
          label: 'Completion Rate',
          status: 'pass',
          description: 'Annual GMP training',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Supplier Qualification',
          value: '91%',
          label: 'Qualified Suppliers',
          status: 'pass',
          description: '185/203 suppliers approved',
          trend: 'up',
          change: '+13%'
        }
      ]
    }
  },

  // GRI Standards Framework
  'gri': {
    frameworkName: 'Global Reporting Initiative (GRI) Standards',
    hero: {
      badge: 'Sustainability Reporting Platform',
      title: ['GRI Standards', ' Compliance', ' Platform'],
      description: 'Achieve comprehensive sustainability reporting with our integrated platform covering GRI Standards framework. Drive transparent ESG disclosure and sustainable business practices.',
      stats: [
        { number: '83%', label: 'GRI Compliance' },
        { number: '8', label: 'Months Implementation' },
        { number: '11', label: 'ESG Policies' },
        { number: '52', label: 'Total Topics' }
      ],
      previewMetrics: [
        {
          title: 'Economic Impact',
          value: '86%',
          change: '+21%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Environmental Impact',
          value: '81%',
          change: '+17%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Social Impact',
          value: '82%',
          change: '+19%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'GRI Standards Implementation Progress',
        percentage: '83%',
        implementationTime: '8 months',
        remainingControls: '17% (GRI)',
        nextAudit: 'Q3 2025',
        policiesLabel: 'ESG Policies',
        policiesValue: '11 Total'
      }
    },
    compliance: {
      title: 'Your GRI Standards Compliance Journey',
      description: 'Track your progress through GRI Standards with real-time monitoring, automated assessments, and expert guidance. Currently at 83% overall disclosure completeness.',
      features: [
        {
          title: 'GRI Standards Assessment',
          description: 'AI-powered assessment of GRI Standards requirements with real-time disclosure scoring and gap analysis.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'ESG Data Collection',
          description: '24/7 monitoring of ESG metrics and data collection across economic, environmental, and social dimensions.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Stakeholder Engagement',
          description: 'Comprehensive stakeholder mapping and engagement tracking for materiality assessment.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'GRI Disclosure Reports',
          description: 'Automated generation of GRI-compliant sustainability reports for investors and stakeholders.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Economic Topics (GRI 200)',
        description: 'Disclose economic performance, market presence, indirect impacts, and procurement practices.',
        compliance: 86,
        controls: 10,
        implemented: 8,
        remaining: 2,
        status: 'completed',
        framework: 'GRI Standards'
      },
      {
        title: 'Environmental Topics (GRI 300)',
        description: 'Report on environmental impact including emissions, water, biodiversity, and waste.',
        compliance: 81,
        controls: 15,
        implemented: 12,
        remaining: 3,
        status: 'completed',
        framework: 'GRI Standards'
      },
      {
        title: 'Social Topics (GRI 400)',
        description: 'Disclose social impact including employment, labor practices, human rights, and community.',
        compliance: 82,
        controls: 16,
        implemented: 13,
        remaining: 3,
        status: 'completed',
        framework: 'GRI Standards'
      },
      {
        title: 'Governance (GRI 2)',
        description: 'Disclose governance structure, ethics, and stakeholder engagement processes.',
        compliance: 85,
        controls: 8,
        implemented: 7,
        remaining: 1,
        status: 'completed',
        framework: 'GRI Standards'
      },
      {
        title: 'Universal Standards (GRI 1-3)',
        description: 'Foundation disclosures including organizational profile, material topics, and management approach.',
        compliance: 83,
        controls: 3,
        implemented: 2,
        remaining: 1,
        status: 'completed',
        framework: 'GRI Standards'
      }
    ],
    benefits: [
      {
        title: 'Accelerated GRI Reporting',
        description: 'Achieve GRI Standards compliance and produce comprehensive sustainability reports in 6-10 months.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'ESG Excellence',
        description: 'Comprehensive ESG disclosure across economic, environmental, and social dimensions.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert ESG Guidance',
        description: 'Access to GRI certified consultants and sustainability experts for implementation support.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Sustainability Reporting',
        description: 'Automated GRI-compliant sustainability reports with integrated ESG data and analytics.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve GRI Standards Compliance?',
      description: 'Join leading organizations worldwide that have implemented GRI Standards with our platform. Start your sustainability reporting journey today.',
      primaryButton: 'Start GRI Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Sustainability Reporting Policy', status: 'Approved', version: '2.4', created_date: '2020-09-15', framework: 'GRI Standards' },
          { id: 2, name: 'Economic Impact Policy', status: 'Approved', version: '2.1', created_date: '2020-10-01', framework: 'GRI Standards' },
          { id: 3, name: 'Environmental Management Policy', status: 'Approved', version: '2.0', created_date: '2020-10-15', framework: 'GRI Standards' },
          { id: 4, name: 'Social Responsibility Policy', status: 'Approved', version: '1.9', created_date: '2020-11-01', framework: 'GRI Standards' }
        ], 
        count: 4, 
        percentage: 56 
      },
      in_progress: { 
        policies: [
          { id: 5, name: 'Stakeholder Engagement Policy', status: 'Under Review', version: '1.6', created_date: '2020-11-15', framework: 'GRI Standards' },
          { id: 6, name: 'Materiality Assessment Policy', status: 'Under Review', version: '1.4', created_date: '2020-12-01', framework: 'GRI Standards' }
        ], 
        count: 2, 
        percentage: 28 
      },
      pending: { 
        policies: [
          { id: 7, name: 'ESG Data Management Policy', status: 'Draft', version: '0.9', created_date: '2020-12-15', framework: 'GRI Standards' }
        ], 
        count: 1, 
        percentage: 16 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'GRI Compliance Score',
          value: '83%',
          label: 'Overall Disclosure',
          status: 'pass',
          description: '52 topics: 43 disclosed, 9 in progress',
          trend: 'up',
          change: '+17%'
        },
        {
          title: 'Economic Impact',
          value: '86%',
          label: 'Topic Coverage',
          status: 'pass',
          description: 'Economic performance and indirect impacts',
          trend: 'up',
          change: '+15%'
        },
        {
          title: 'Environmental Impact',
          value: '81%',
          label: 'Topic Coverage',
          status: 'pass',
          description: 'Emissions, water, biodiversity',
          trend: 'up',
          change: '+18%'
        },
        {
          title: 'Social Impact',
          value: '82%',
          label: 'Topic Coverage',
          status: 'pass',
          description: 'Employment, human rights, community',
          trend: 'up',
          change: '+16%'
        },
        {
          title: 'Stakeholder Engagement',
          value: '92%',
          label: 'Engagement Rate',
          status: 'pass',
          description: 'Regular engagement with key stakeholders',
          trend: 'up',
          change: '+10%'
        },
        {
          title: 'Material Topics',
          value: '14',
          label: 'Identified Topics',
          status: 'pass',
          description: 'Material topics confirmed',
          trend: 'up',
          change: '+27%'
        },
        {
          title: 'Data Quality',
          value: '94%',
          label: 'Accuracy Score',
          status: 'pass',
          description: 'Third-party verified data',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Report Timeliness',
          value: '100%',
          label: 'On-Time Release',
          status: 'pass',
          description: 'Published within annual cycle',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Assurance Level',
          value: 'Limited',
          label: 'GRI Assurance',
          status: 'monitor',
          description: 'Working toward reasonable assurance',
          trend: 'up',
          change: '+18%'
        },
        {
          title: 'UN SDG Alignment',
          value: '13',
          label: 'SDGs Addressed',
          status: 'pass',
          description: 'Out of 17 UN SDGs',
          trend: 'up',
          change: '+30%'
        }
      ]
    }
  },

  // MAS TRM Framework
  'mastrm': {
    frameworkName: 'MAS TRM',
    hero: {
      badge: 'Technology Risk Management Platform',
      title: ['MAS Technology Risk', ' Management', ' Compliance'],
      description: 'Achieve comprehensive technology risk management compliance with Monetary Authority of Singapore (MAS) TRM guidelines. Drive robust technology risk governance and resilience in financial services.',
      stats: [
        { number: '88%', label: 'MAS TRM Compliance' },
        { number: '11', label: 'Months Implementation' },
        { number: '16', label: 'Risk Policies' },
        { number: '48', label: 'Risk Controls' }
      ],
      previewMetrics: [
        {
          title: 'Technology Risk Governance',
          value: '92%',
          change: '+17%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Cyber Resilience',
          value: '87%',
          change: '+14%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Operations Resilience',
          value: '85%',
          change: '+16%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'MAS TRM Implementation Progress',
        percentage: '88%',
        implementationTime: '11 months',
        remainingControls: '12% (MAS TRM)',
        nextAudit: 'Q1 2025',
        policiesLabel: 'Risk Policies',
        policiesValue: '16 Total'
      }
    },
    compliance: {
      title: 'Your MAS TRM Compliance Journey',
      description: 'Track your progress through MAS Technology Risk Management guidelines with real-time monitoring, automated assessments, and expert guidance. Currently at 88% overall compliance.',
      features: [
        {
          title: 'MAS TRM Risk Assessment',
          description: 'AI-powered assessment of MAS technology risk management requirements with real-time compliance scoring and gap analysis.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Technology Risk Monitoring',
          description: '24/7 monitoring of technology risks, cyber threats, and operational resilience with automated alerts.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Risk Governance Framework',
          description: 'Comprehensive technology risk governance with board oversight and management accountability.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'MAS Regulatory Reporting',
          description: 'Automated generation of MAS compliance reports and regulatory submissions with complete evidence.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Technology Risk Governance',
        description: 'Establish board and management oversight of technology risk with clear accountability and responsibilities.',
        compliance: 91,
        controls: 8,
        implemented: 7,
        remaining: 1,
        status: 'completed',
        framework: 'MAS TRM'
      },
      {
        title: 'Cyber Resilience',
        description: 'Implement robust cybersecurity controls and incident response capabilities for financial services.',
        compliance: 87,
        controls: 12,
        implemented: 10,
        remaining: 2,
        status: 'completed',
        framework: 'MAS TRM'
      },
      {
        title: 'Operations Resilience',
        description: 'Ensure operational continuity and disaster recovery capabilities for critical business functions.',
        compliance: 85,
        controls: 10,
        implemented: 8,
        remaining: 2,
        status: 'completed',
        framework: 'MAS TRM'
      },
      {
        title: 'Technology Outsourcing',
        description: 'Manage technology outsourcing risks with vendor due diligence and ongoing monitoring.',
        compliance: 90,
        controls: 9,
        implemented: 8,
        remaining: 1,
        status: 'completed',
        framework: 'MAS TRM'
      },
      {
        title: 'Technology Operations',
        description: 'Implement robust technology operations including system development, change management, and access controls.',
        compliance: 82,
        controls: 11,
        implemented: 9,
        remaining: 2,
        status: 'in-progress',
        framework: 'MAS TRM'
      },
      {
        title: 'Incident Management',
        description: 'Establish technology incident response and escalation procedures for timely resolution.',
        compliance: 88,
        controls: 7,
        implemented: 6,
        remaining: 1,
        status: 'completed',
        framework: 'MAS TRM'
      }
    ],
    benefits: [
      {
        title: 'Accelerated MAS TRM Compliance',
        description: 'Achieve MAS technology risk management compliance in 8-12 months with our proven methodology.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Technology Risk Excellence',
        description: 'Comprehensive technology risk management aligned with MAS guidelines for financial institutions.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert MAS Guidance',
        description: 'Access to MAS compliance experts with deep knowledge of Singapore banking regulations.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Regulatory Reporting',
        description: 'Automated MAS compliance reports and regulatory submissions with complete documentation.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve MAS TRM Compliance?',
      description: 'Join leading financial institutions in Singapore that have achieved MAS TRM compliance with our platform. Start your technology risk management journey today.',
      primaryButton: 'Start MAS TRM Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Technology Risk Governance Policy', status: 'Approved', version: '3.1', created_date: '2022-01-10', framework: 'MAS TRM' },
          { id: 2, name: 'Cybersecurity Policy', status: 'Approved', version: '2.9', created_date: '2022-02-01', framework: 'MAS TRM' },
          { id: 3, name: 'Operations Resilience Policy', status: 'Approved', version: '2.7', created_date: '2022-03-01', framework: 'MAS TRM' },
          { id: 4, name: 'Technology Outsourcing Policy', status: 'Approved', version: '2.5', created_date: '2022-04-01', framework: 'MAS TRM' },
          { id: 5, name: 'Technology Operations Policy', status: 'Approved', version: '2.3', created_date: '2022-05-01', framework: 'MAS TRM' }
        ], 
        count: 5, 
        percentage: 59 
      },
      in_progress: { 
        policies: [
          { id: 6, name: 'Incident Management Policy', status: 'Under Review', version: '2.0', created_date: '2022-06-01', framework: 'MAS TRM' },
          { id: 7, name: 'Change Management Policy', status: 'Under Review', version: '1.8', created_date: '2022-07-01', framework: 'MAS TRM' }
        ], 
        count: 2, 
        percentage: 24 
      },
      pending: { 
        policies: [
          { id: 8, name: 'Third-Party Risk Management Policy', status: 'Draft', version: '1.0', created_date: '2022-08-01', framework: 'MAS TRM' }
        ], 
        count: 1, 
        percentage: 17 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'Technology Risk Governance',
          value: '91%',
          label: 'Board Oversight',
          status: 'pass',
          description: 'Board and senior management accountability',
          trend: 'up',
          change: '+12%'
        },
        {
          title: 'Cybersecurity Controls',
          value: '87%',
          label: 'Implementation Rate',
          status: 'pass',
          description: '12 cybersecurity controls implemented',
          trend: 'up',
          change: '+15%'
        },
        {
          title: 'Operations Resilience',
          value: '85%',
          label: 'Continuity Coverage',
          status: 'pass',
          description: 'Critical systems covered',
          trend: 'up',
          change: '+13%'
        },
        {
          title: 'Technology Outsourcing',
          value: '90%',
          label: 'Risk Assessment',
          status: 'pass',
          description: 'Vendor due diligence completed',
          trend: 'up',
          change: '+11%'
        },
        {
          title: 'Change Management',
          value: '94%',
          label: 'Change Success Rate',
          status: 'pass',
          description: 'System changes properly tested',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Access Control',
          value: '89%',
          label: 'User Access Reviews',
          status: 'pass',
          description: 'Quarterly reviews completed',
          trend: 'up',
          change: '+10%'
        },
        {
          title: 'Incident Response',
          value: '2.5h',
          label: 'Mean Response Time',
          status: 'pass',
          description: 'Average incident resolution time',
          trend: 'down',
          change: '-18%'
        },
        {
          title: 'Vulnerability Management',
          value: '96%',
          label: 'Patch Coverage',
          status: 'pass',
          description: 'Critical patches applied',
          trend: 'up',
          change: '+6%'
        },
        {
          title: 'Backup & Recovery',
          value: '99.5%',
          label: 'Backup Success Rate',
          status: 'pass',
          description: 'Daily backup verification',
          trend: 'up',
          change: '+0.3%'
        },
        {
          title: 'Regulatory Reporting',
          value: '100%',
          label: 'MAS Submissions',
          status: 'pass',
          description: 'All submissions on time',
          trend: 'stable',
          change: '0%'
        }
      ]
    }
  },

  // ISO 27011 Framework
  'iso27011': {
    frameworkName: 'ISO 27011',
    hero: {
      badge: 'Information Security Control Platform',
      title: ['Information Security', ' Controls', ' with ISO 27011'],
      description: 'Achieve comprehensive information security control implementation with our integrated platform covering ISO 27011 framework. Drive security excellence with practical control guidance.',
      stats: [
        { number: '93%', label: 'ISO 27011 Compliance' },
        { number: '10', label: 'Months Implementation' },
        { number: '13', label: 'Security Policies' },
        { number: '126', label: 'Security Controls' }
      ],
      previewMetrics: [
        {
          title: 'Information Security',
          value: '96%',
          change: '+19%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Risk Management',
          value: '91%',
          change: '+14%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Access Control',
          value: '94%',
          change: '+16%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'ISO 27011 Implementation Progress',
        percentage: '93%',
        implementationTime: '10 months',
        remainingControls: '7% (ISO 27011)',
        nextAudit: 'Q1 2025',
        policiesLabel: 'Security Policies',
        policiesValue: '13 Total'
      }
    },
    compliance: {
      title: 'Your ISO 27011 Compliance Journey',
      description: 'Track your progress through ISO 27011 framework with real-time monitoring, automated assessments, and expert guidance. Currently at 93% overall compliance.',
      features: [
        {
          title: 'ISO 27011 Control Assessment',
          description: 'AI-powered assessment of ISO 27011 information security controls with real-time compliance scoring and gap analysis.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Continuous Security Monitoring',
          description: '24/7 monitoring of information security controls, threats, and vulnerabilities with automated alerts.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Security Risk Assessment',
          description: 'Comprehensive information security risk assessment with threat modeling and treatment planning.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'Control Implementation Guidance',
          description: 'Practical guidance and templates for implementing ISO 27011 controls with best practices.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Information Security Policies',
        description: 'Develop and maintain comprehensive information security policies aligned with ISO 27011.',
        compliance: 97,
        controls: 7,
        implemented: 7,
        remaining: 0,
        status: 'completed',
        framework: 'ISO 27011'
      },
      {
        title: 'Organization of Information Security',
        description: 'Establish information security roles, responsibilities, and governance structure.',
        compliance: 95,
        controls: 9,
        implemented: 8,
        remaining: 1,
        status: 'completed',
        framework: 'ISO 27011'
      },
      {
        title: 'Human Resource Security',
        description: 'Implement security controls for personnel security, background checks, and training.',
        compliance: 93,
        controls: 8,
        implemented: 7,
        remaining: 1,
        status: 'completed',
        framework: 'ISO 27011'
      },
      {
        title: 'Asset Management',
        description: 'Identify, classify, and protect information assets with appropriate controls.',
        compliance: 96,
        controls: 5,
        implemented: 5,
        remaining: 0,
        status: 'completed',
        framework: 'ISO 27011'
      },
      {
        title: 'Access Control',
        description: 'Implement user access management, authentication, and privilege management controls.',
        compliance: 94,
        controls: 16,
        implemented: 15,
        remaining: 1,
        status: 'completed',
        framework: 'ISO 27011'
      },
      {
        title: 'Cryptography',
        description: 'Establish cryptographic controls and key management for information protection.',
        compliance: 92,
        controls: 6,
        implemented: 5,
        remaining: 1,
        status: 'in-progress',
        framework: 'ISO 27011'
      }
    ],
    benefits: [
      {
        title: 'Accelerated ISO 27011 Implementation',
        description: 'Achieve ISO 27011 compliance in 6-12 months with our proven methodology and control templates.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Enhanced Information Security',
        description: 'Comprehensive information security controls with continuous monitoring and incident response.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert Security Guidance',
        description: 'Access to ISO 27011 certified consultants and information security experts for implementation support.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Control Implementation Templates',
        description: 'Practical templates and guidance for implementing ISO 27011 controls effectively.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Achieve ISO 27011 Compliance?',
      description: 'Join organizations worldwide that have implemented ISO 27011 with our platform. Start your information security journey today.',
      primaryButton: 'Start ISO 27011 Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Information Security Policy', status: 'Approved', version: '3.1', created_date: '2022-02-10', framework: 'ISO 27011' },
          { id: 2, name: 'Access Control Policy', status: 'Approved', version: '2.9', created_date: '2022-03-01', framework: 'ISO 27011' },
          { id: 3, name: 'Cryptography Policy', status: 'Approved', version: '2.2', created_date: '2022-03-15', framework: 'ISO 27011' },
          { id: 4, name: 'Physical Security Policy', status: 'Approved', version: '2.0', created_date: '2022-04-01', framework: 'ISO 27011' },
          { id: 5, name: 'Operations Security Policy', status: 'Approved', version: '2.6', created_date: '2022-04-15', framework: 'ISO 27011' }
        ], 
        count: 5, 
        percentage: 62 
      },
      in_progress: { 
        policies: [
          { id: 6, name: 'Communications Security Policy', status: 'Under Review', version: '1.8', created_date: '2022-05-01', framework: 'ISO 27011' },
          { id: 7, name: 'Supplier Relationship Policy', status: 'Under Review', version: '1.6', created_date: '2022-05-15', framework: 'ISO 27011' }
        ], 
        count: 2, 
        percentage: 25 
      },
      pending: { 
        policies: [
          { id: 8, name: 'Compliance & Audit Policy', status: 'Draft', version: '0.9', created_date: '2022-06-01', framework: 'ISO 27011' }
        ], 
        count: 1, 
        percentage: 13 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'Control Implementation',
          value: '93%',
          label: 'Controls Implemented',
          status: 'pass',
          description: '126 controls: 117 implemented, 9 in progress',
          trend: 'up',
          change: '+18%'
        },
        {
          title: 'Information Security Incidents',
          value: '3',
          label: 'Monthly Average',
          status: 'pass',
          description: 'Average response time: 1.6 hours',
          trend: 'down',
          change: '-33%'
        },
        {
          title: 'Vulnerability Management',
          value: '98%',
          label: 'Remediation Rate',
          status: 'pass',
          description: 'Critical: 100%, High: 98%, Medium: 94%',
          trend: 'up',
          change: '+12%'
        },
        {
          title: 'Access Control Compliance',
          value: '99%',
          label: 'User Access Reviews',
          status: 'pass',
          description: 'Quarterly reviews: 99% completion',
          trend: 'up',
          change: '+2%'
        },
        {
          title: 'Security Awareness Training',
          value: '96%',
          label: 'Completion Rate',
          status: 'pass',
          description: 'Annual training: 672/700 employees',
          trend: 'up',
          change: '+9%'
        },
        {
          title: 'Risk Assessment Coverage',
          value: '95%',
          label: 'Assets Assessed',
          status: 'pass',
          description: '171/180 critical assets assessed',
          trend: 'up',
          change: '+21%'
        },
        {
          title: 'Audit Findings',
          value: '5',
          label: 'Open Findings',
          status: 'pass',
          description: 'High: 0, Medium: 3, Low: 2',
          trend: 'down',
          change: '-38%'
        },
        {
          title: 'Encryption Coverage',
          value: '100%',
          label: 'Data at Rest',
          status: 'pass',
          description: 'All sensitive data encrypted',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Backup Success Rate',
          value: '99.95%',
          label: 'Monthly Average',
          status: 'pass',
          description: 'Last failed backup: 28 days ago',
          trend: 'up',
          change: '+0.15%'
        },
        {
          title: 'Patch Management',
          value: '96%',
          label: 'Systems Up-to-Date',
          status: 'pass',
          description: 'Critical patches: 100%, Security: 98%',
          trend: 'up',
          change: '+11%'
        }
      ]
    }
  },

  // TCFD Framework
  'tcfd': {
    frameworkName: 'TCFD',
    hero: {
      badge: 'Climate Risk Disclosure Platform',
      title: ['Climate-Related', ' Financial Disclosures', ' with TCFD Framework'],
      description: 'Achieve comprehensive climate-related financial disclosure with our integrated platform covering TCFD framework. Drive transparency in climate risk management and opportunity identification.',
      stats: [
        { number: '78%', label: 'TCFD Disclosure' },
        { number: '7', label: 'Months Implementation' },
        { number: '11', label: 'Climate Policies' },
        { number: '4', label: 'Core Pillars' }
      ],
      previewMetrics: [
        {
          title: 'Governance',
          value: '85%',
          change: '+15%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Strategy',
          value: '75%',
          change: '+10%',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Risk Management',
          value: '72%',
          change: '+8%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'TCFD Implementation Progress',
        percentage: '78%',
        implementationTime: '7 months',
        remainingControls: '22% (TCFD)',
        nextAudit: 'Q3 2025',
        policiesLabel: 'Climate Policies',
        policiesValue: '11 Total'
      }
    },
    compliance: {
      title: 'Your TCFD Compliance Journey',
      description: 'Track your progress through TCFD framework with real-time monitoring, automated assessments, and expert guidance. Currently at 78% overall disclosure completeness.',
      features: [
        {
          title: 'Climate Risk Assessment',
          description: 'Comprehensive climate risk identification and assessment with scenario analysis and materiality evaluation.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Scenario Analysis',
          description: 'Advanced climate scenario modeling including 1.5°C, 2°C, and 4°C pathways with financial impact analysis.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Metrics & Targets',
          description: 'Track climate-related metrics including GHG emissions, energy use, and transition risk indicators.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'TCFD Disclosure Reports',
          description: 'Automated generation of TCFD-aligned disclosure reports for investors and stakeholders.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Governance',
        description: 'Describe board oversight and management role in assessing and managing climate-related risks.',
        compliance: 85,
        controls: 4,
        implemented: 3,
        remaining: 1,
        status: 'completed',
        framework: 'TCFD'
      },
      {
        title: 'Strategy',
        description: 'Disclose climate-related risks and opportunities and their impact on business, strategy, and planning.',
        compliance: 75,
        controls: 6,
        implemented: 4,
        remaining: 2,
        status: 'in-progress',
        framework: 'TCFD'
      },
      {
        title: 'Risk Management',
        description: 'Describe processes for identifying, assessing, and managing climate-related risks.',
        compliance: 72,
        controls: 5,
        implemented: 3,
        remaining: 2,
        status: 'in-progress',
        framework: 'TCFD'
      },
      {
        title: 'Metrics and Targets',
        description: 'Disclose metrics and targets used to assess and manage climate-related risks and opportunities.',
        compliance: 80,
        controls: 7,
        implemented: 5,
        remaining: 2,
        status: 'completed',
        framework: 'TCFD'
      }
    ],
    benefits: [
      {
        title: 'Enhanced Climate Disclosure',
        description: 'Achieve comprehensive TCFD-aligned climate disclosure in 6-10 months with our expert methodology.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Investor Confidence',
        description: 'Build investor confidence with transparent climate risk disclosure and strategic climate response.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert Climate Guidance',
        description: 'Access to climate risk experts with deep knowledge of TCFD, scenario analysis, and disclosure requirements.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Comprehensive Reporting',
        description: 'Automated TCFD disclosure reports with integrated climate risk data and scenario analysis.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Enhance Climate Disclosure?',
      description: 'Join leading organizations worldwide that have implemented TCFD-aligned climate disclosure with our platform. Start your climate transparency journey today.',
      primaryButton: 'Start TCFD Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { 
        policies: [
          { id: 1, name: 'Climate Governance Policy', status: 'Approved', version: '2.3', created_date: '2020-09-01', framework: 'TCFD' },
          { id: 2, name: 'Climate Risk Assessment Policy', status: 'Approved', version: '2.1', created_date: '2020-10-01', framework: 'TCFD' },
          { id: 3, name: 'Scenario Analysis Policy', status: 'Approved', version: '1.9', created_date: '2020-11-01', framework: 'TCFD' },
          { id: 4, name: 'Climate Metrics and Targets Policy', status: 'Approved', version: '2.0', created_date: '2020-12-01', framework: 'TCFD' }
        ], 
        count: 4, 
        percentage: 57 
      },
      in_progress: { 
        policies: [
          { id: 5, name: 'Climate Strategy Integration Policy', status: 'Under Review', version: '1.5', created_date: '2021-01-01', framework: 'TCFD' },
          { id: 6, name: 'Climate Opportunity Management Policy', status: 'Under Review', version: '1.3', created_date: '2021-02-01', framework: 'TCFD' }
        ], 
        count: 2, 
        percentage: 29 
      },
      pending: { 
        policies: [
          { id: 7, name: 'Climate Disclosure Policy', status: 'Draft', version: '0.8', created_date: '2021-03-01', framework: 'TCFD' }
        ], 
        count: 1, 
        percentage: 14 
      }
    },
    kpis: {
      showKPIs: true,
      kpiSections: [
        {
          title: 'TCFD Disclosure Completeness',
          value: '78%',
          label: 'Overall Disclosure',
          status: 'monitor',
          description: 'All 4 pillars partially implemented',
          trend: 'up',
          change: '+15%'
        },
        {
          title: 'Governance Pillar',
          value: '85%',
          label: 'Board Oversight',
          status: 'pass',
          description: 'Climate governance established',
          trend: 'up',
          change: '+10%'
        },
        {
          title: 'Strategy Pillar',
          value: '75%',
          label: 'Strategic Integration',
          status: 'monitor',
          description: 'Risks and opportunities identified',
          trend: 'up',
          change: '+12%'
        },
        {
          title: 'Risk Management Pillar',
          value: '72%',
          label: 'Process Integration',
          status: 'monitor',
          description: 'Climate risk processes defined',
          trend: 'up',
          change: '+8%'
        },
        {
          title: 'Metrics & Targets Pillar',
          value: '80%',
          label: 'Data Collection',
          status: 'pass',
          description: 'Key metrics being tracked',
          trend: 'up',
          change: '+18%'
        },
        {
          title: 'GHG Emissions (Scope 1)',
          value: '2,350',
          label: 'Tonnes CO2e',
          status: 'monitor',
          description: 'Direct emissions tracked',
          trend: 'down',
          change: '-5%'
        },
        {
          title: 'GHG Emissions (Scope 2)',
          value: '4,120',
          label: 'Tonnes CO2e',
          status: 'monitor',
          description: 'Indirect emissions tracked',
          trend: 'down',
          change: '-8%'
        },
        {
          title: 'GHG Emissions (Scope 3)',
          value: '12,890',
          label: 'Tonnes CO2e',
          status: 'monitor',
          description: 'Value chain emissions partial',
          trend: 'down',
          change: '-3%'
        },
        {
          title: 'Scenario Analysis Coverage',
          value: '3',
          label: 'Scenarios Modeled',
          status: 'pass',
          description: '1.5°C, 2°C, and 4°C pathways',
          trend: 'stable',
          change: '0%'
        },
        {
          title: 'Climate Resilience Score',
          value: '72%',
          label: 'Overall Resilience',
          status: 'monitor',
          description: 'Physical and transition risks assessed',
          trend: 'up',
          change: '+10%'
        }
      ]
    }
  },

  // Default/All Frameworks
  'all': {
    frameworkName: 'All Frameworks',
    hero: {
      badge: 'Multi-Framework GRC Platform',
      title: ['Enterprise GRC', ' Platform', ' for All Compliance Needs'],
      description: 'Achieve comprehensive compliance across multiple frameworks with our integrated platform. Manage Basel 3, ISO 27001, NIST 800-53, PCI DSS, and TCFD from a single unified dashboard.',
      stats: [
        { number: '5', label: 'Active Frameworks' },
        { number: '84%', label: 'Average Compliance' },
        { number: '56', label: 'Total Policies' },
        { number: '528', label: 'Total Controls' }
      ],
      previewMetrics: [
        {
          title: 'Overall Compliance',
          value: '84%',
          change: '+11%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Active Policies',
          value: '56',
          change: '+8',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Risk Coverage',
          value: '88%',
          change: '+15%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: 'Multi-Framework Implementation Progress',
        percentage: '84%',
        implementationTime: '12 months (avg)',
        remainingControls: '16% (All Frameworks)',
        nextAudit: 'Rolling Schedule',
        policiesLabel: 'Total Policies',
        policiesValue: '56 Across All Frameworks'
      }
    },
    compliance: {
      title: 'Your Multi-Framework Compliance Journey',
      description: 'Track your progress across all frameworks with unified monitoring, automated assessments, and expert guidance. Currently at 84% average compliance across all active frameworks.',
      features: [
        {
          title: 'Unified Framework Management',
          description: 'Manage Basel 3, ISO 27001, NIST 800-53, PCI DSS, and TCFD from a single centralized platform with cross-framework insights.',
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Cross-Framework Monitoring',
          description: '24/7 monitoring of all compliance frameworks with consolidated dashboards and unified alert management.',
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Integrated Risk Assessment',
          description: 'Comprehensive risk assessment across all frameworks with correlation analysis and unified risk scoring.',
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'Consolidated Reporting',
          description: 'Generate unified compliance reports across all frameworks or framework-specific detailed reports for stakeholders.',
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: 'Financial Risk Management (Basel 3)',
        description: 'Capital adequacy, liquidity risk, and leverage ratio compliance for banking regulations.',
        compliance: 76,
        controls: 27,
        implemented: 19,
        remaining: 8,
        status: 'in-progress',
        framework: 'Basel 3'
      },
      {
        title: 'Information Security (ISO 27001)',
        description: 'Comprehensive information security management system with 93 security controls.',
        compliance: 89,
        controls: 93,
        implemented: 76,
        remaining: 17,
        status: 'completed',
        framework: 'ISO 27001:2022'
      },
      {
        title: 'Federal Security (NIST 800-53)',
        description: 'Federal security compliance with 325 controls for government systems and contractors.',
        compliance: 82,
        controls: 325,
        implemented: 267,
        remaining: 58,
        status: 'completed',
        framework: 'NIST 800-53'
      },
      {
        title: 'Payment Security (PCI DSS)',
        description: 'Payment card industry data security with 12 requirements for cardholder data protection.',
        compliance: 91,
        controls: 50,
        implemented: 46,
        remaining: 4,
        status: 'completed',
        framework: 'PCI DSS'
      },
      {
        title: 'Climate Disclosure (TCFD)',
        description: 'Climate-related financial disclosures with 4 pillars for transparent risk reporting.',
        compliance: 78,
        controls: 22,
        implemented: 17,
        remaining: 5,
        status: 'in-progress',
        framework: 'TCFD'
      }
    ],
    benefits: [
      {
        title: 'Unified Framework Management',
        description: 'Manage multiple compliance frameworks from a single platform, reducing complexity and operational overhead.',
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Comprehensive Risk Coverage',
        description: 'Complete coverage of financial, security, payment, and climate risks across all regulatory frameworks.',
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Expert Multi-Domain Guidance',
        description: 'Access to compliance experts across all frameworks including Basel 3, ISO 27001, NIST, PCI DSS, and TCFD.',
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Consolidated Reporting',
        description: 'Unified compliance dashboards and cross-framework reports for complete organizational visibility.',
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: 'Ready to Streamline Multi-Framework Compliance?',
      description: 'Join organizations worldwide managing multiple compliance frameworks with our unified platform. Achieve comprehensive compliance across all regulatory requirements.',
      primaryButton: 'Start Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { policies: [], count: 39, percentage: 70 },
      in_progress: { policies: [], count: 10, percentage: 18 },
      pending: { policies: [], count: 7, percentage: 12 }
    },
    kpis: {
      showBaselKPIs: false,
      showKPIs: false
    }
  }
};

// Map framework IDs to content keys
export const frameworkIdMap = {
  'all': 'all',
  // Common framework name variations
  'Basel 3': 'basel3',
  'Basel III': 'basel3',
  'Basel3': 'basel3',
  'ISO 27001:2022': 'iso27001',
  'ISO 27001': 'iso27001',
  'ISO27001': 'iso27001',
  'ISO 27011': 'iso27011',
  'ISO27011': 'iso27011',
  'NIST 800-53': 'nist80053',
  'NIST80053': 'nist80053',
  'PCI DSS': 'pcidss',
  'PCIDSS': 'pcidss',
  'TCFD': 'tcfd',
  'Task Force on Climate-related Financial Disclosures': 'tcfd',
  // FDA
  'Food and Drug Administration': 'fda',
  'FDA': 'fda',
  // GRI
  'Global Reporting Initiative (GRI) Standards': 'gri',
  'GRI Standards': 'gri',
  'GRI': 'gri',
  // MAS TRM
  'MAS TRM': 'mastrm',
  'MAS Technology Risk Management': 'mastrm',
  'Monetary Authority of Singapore TRM': 'mastrm',
  // Add actual framework IDs from your database here
  // These should match the FrameworkId values from your backend
};

// Generate generic framework content for frameworks without specific definitions
function generateGenericFrameworkContent(frameworkName) {
  console.log('🔧 Generating generic content for:', frameworkName);
  
  return {
    frameworkName: frameworkName,
    hero: {
      badge: 'GRC Compliance Platform',
      title: ['Enterprise GRC', ' Platform', ` for ${frameworkName}`],
      description: `Achieve comprehensive compliance with our integrated platform covering ${frameworkName} framework. Drive regulatory alignment and risk management excellence with automated monitoring and expert guidance.`,
      stats: [
        { number: '0%', label: `${frameworkName} Compliance` },
        { number: '0', label: 'Months Implementation' },
        { number: '0', label: `${frameworkName} Policies` },
        { number: '0', label: 'Total Controls' }
      ],
      previewMetrics: [
        {
          title: 'Overall Compliance',
          value: '0%',
          change: '+0%',
          trend: 'positive',
          color: 'green',
          type: 'shield'
        },
        {
          title: 'Active Policies',
          value: '0',
          change: '+0',
          trend: 'positive',
          color: 'blue',
          type: 'check'
        },
        {
          title: 'Risk Coverage',
          value: '0%',
          change: '+0%',
          trend: 'positive',
          color: 'orange',
          type: 'alert'
        }
      ],
      previewCard: {
        title: `${frameworkName} Implementation Progress`,
        percentage: '0%',
        implementationTime: '0 months',
        remainingControls: '0%',
        nextAudit: 'TBD',
        policiesLabel: `${frameworkName} Policies`,
        policiesValue: '0 Total'
      }
    },
    compliance: {
      title: `Your ${frameworkName} Compliance Journey`,
      description: `Track your progress through ${frameworkName} framework with real-time monitoring, automated assessments, and expert guidance. Monitor your compliance status and implementation progress.`,
      features: [
        {
          title: `Automated ${frameworkName} Assessment`,
          description: `AI-powered assessment of ${frameworkName} controls with real-time compliance scoring and gap analysis.`,
          color: 'green',
          type: 'automation'
        },
        {
          title: 'Continuous Monitoring',
          description: `24/7 monitoring of ${frameworkName} compliance metrics, controls, and risk indicators with automated alerts.`,
          color: 'blue',
          type: 'monitoring'
        },
        {
          title: 'Comprehensive Risk Assessment',
          description: `Detailed risk assessment specific to ${frameworkName} requirements with gap analysis and mitigation planning.`,
          color: 'purple',
          type: 'assessment'
        },
        {
          title: 'Regulatory Reporting',
          description: `Automated generation of ${frameworkName} compliance reports for regulators, auditors, and stakeholders with customizable dashboards.`,
          color: 'orange',
          type: 'reporting'
        }
      ]
    },
    domains: [
      {
        title: `${frameworkName} Control Domain`,
        description: `Comprehensive coverage of ${frameworkName} control domains with detailed implementation status and metrics.`,
        compliance: 0,
        controls: 0,
        implemented: 0,
        remaining: 0,
        status: 'pending',
        framework: frameworkName
      }
    ],
    benefits: [
      {
        title: `${frameworkName} Compliance Management`,
        description: `Streamline your ${frameworkName} compliance efforts with automated workflows and centralized management.`,
        color: 'green',
        type: 'clock'
      },
      {
        title: 'Expert Guidance',
        description: `Access to compliance experts and best practices specific to ${frameworkName} requirements.`,
        color: 'blue',
        type: 'shield'
      },
      {
        title: 'Automated Assessments',
        description: `AI-powered assessment tools designed for ${frameworkName} framework compliance.`,
        color: 'purple',
        type: 'users'
      },
      {
        title: 'Real-time Monitoring',
        description: `Continuous monitoring and reporting of ${frameworkName} compliance status and metrics.`,
        color: 'orange',
        type: 'chart'
      }
    ],
    cta: {
      title: `Ready to Achieve ${frameworkName} Compliance?`,
      description: `Join organizations worldwide achieving ${frameworkName} compliance with our integrated platform. Start your compliance journey today.`,
      primaryButton: 'Start Implementation',
      secondaryButton: 'Schedule Demo'
    },
    policies: {
      applied: { policies: [], count: 0, percentage: 0 },
      in_progress: { policies: [], count: 0, percentage: 0 },
      pending: { policies: [], count: 0, percentage: 0 },
      rejected: { policies: [], count: 0, percentage: 0 }
    },
    kpis: {
      showBaselKPIs: false,
      showKPIs: false
    }
  };
}

// Helper function to get content by framework ID or name
export function getFrameworkContent(frameworkId) {
  console.log('🔍 getFrameworkContent called with:', frameworkId);
  
  // Handle 'all' or null/undefined
  if (!frameworkId || frameworkId === 'all') {
    console.log('📦 Returning "All Frameworks" content');
    return frameworkContent['all'];
  }
  
  // First try explicit mapping
  let contentKey = frameworkIdMap[frameworkId];
  
  if (contentKey) {
    console.log('✅ Found explicit mapping:', frameworkId, '->', contentKey);
    // If we have specific content for this key, use it
    if (frameworkContent[contentKey]) {
      console.log('📦 Content key resolved to:', contentKey);
      console.log('📋 Framework name:', frameworkContent[contentKey].frameworkName);
      return frameworkContent[contentKey];
    }
  } else {
    // Fall back to pattern matching
    contentKey = getContentKeyByName(frameworkId);
    console.log('🔄 Used pattern matching:', frameworkId, '->', contentKey);
    
    // If pattern matching found a key and content exists, use it
    if (contentKey && frameworkContent[contentKey]) {
      console.log('📦 Content key resolved to:', contentKey);
      console.log('📋 Framework name:', frameworkContent[contentKey].frameworkName);
      return frameworkContent[contentKey];
    }
  }
  
  // Otherwise, generate generic content with the framework name
  console.log('⚠️ No specific content found for:', frameworkId);
  console.log('🔧 Generating generic content with framework name:', frameworkId);
  const genericContent = generateGenericFrameworkContent(frameworkId);
  console.log('✅ Generated generic content for:', genericContent.frameworkName);
  return genericContent;
}

// Helper function to match framework by name or ID
function getContentKeyByName(frameworkId) {
  if (!frameworkId || frameworkId === 'all') return 'all';
  
  // Convert to string and lowercase for comparison
  const idLower = frameworkId.toString().toLowerCase();
  
  console.log('🔍 Matching framework:', frameworkId, '-> lowercase:', idLower);
  
  // Match by framework name patterns (more flexible matching)
  // Note: Check more specific patterns first to avoid false matches
  // FATF - Must check BEFORE TCFD because both contain "task force"
  if (idLower.includes('fatf') || (idLower.includes('financial action') && idLower.includes('task force'))) return null; // Will use generic content
  // Basel
  if (idLower.includes('basel') || idLower.includes('basel 3') || idLower.includes('basel iii')) return 'basel3';
  // ISO 27011 - Must check before ISO 27001
  if (idLower.includes('iso') && idLower.includes('27011')) return 'iso27011';
  // ISO 27001
  if (idLower.includes('iso') && (idLower.includes('27001') || idLower.includes('27002'))) return 'iso27001';
  // NIST
  if (idLower.includes('nist') && idLower.includes('800')) return 'nist80053';
  // PCI DSS
  if (idLower.includes('pci') || idLower.includes('dss') || idLower.includes('payment card')) return 'pcidss';
  // TCFD - Must be more specific to avoid matching FATF (both have "task force")
  // Only match if it's specifically about climate-related financial disclosures
  if (idLower.includes('tcfd') || (idLower.includes('task force') && idLower.includes('climate'))) return 'tcfd';
  // FDA
  if (idLower.includes('food and drug') || idLower.includes('fda')) return 'fda';
  // GRI
  if (idLower.includes('gri') || idLower.includes('global reporting initiative')) return 'gri';
  // MAS TRM
  if (idLower.includes('mas trm') || idLower.includes('mas technology risk') || idLower.includes('monetary authority singapore')) return 'mastrm';
  
  console.log('⚠️ No pattern match found for:', frameworkId, 'will use generic content');
  // Return null to indicate no match - getFrameworkContent will generate generic content
  return null;
}

// Helper function to get framework name from approved framework object
export function getFrameworkKey(framework) {
  if (!framework) return 'all';
  
  // Try to match by framework name
  const frameworkName = framework.FrameworkName || framework.name || '';
  return getContentKeyByName(frameworkName);
}

