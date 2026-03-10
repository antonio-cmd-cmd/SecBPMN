export const knowledgeBaseLLMdescription = [
    {
        principle: "Confidentiality",
        threats: [
            {
                threat: "Unauthorized Confidential Data Acquisition",
                description: "(Data that is being stolen or used inappropriately its in this category. The attack can target not only a computer system but also a web service when for instance a session is being hijacked.) An insider intentionally or unintentionally obtains confidential data through unauthorized means, such as stealing sensitive information from computer systems, business applications, or online services. This threat includes cases where session hijacking, credential misuse, or exploiting system vulnerabilities enables the insider to access data that exceeds their authorized usage. Business processes that handle confidential data are expected to ensure that access is strictly controlled and monitored, but this threat undermines confidentiality by bypassing these safeguards."
            },
            {
                threat: "Inappropriate Confidential Data Viewing",
                description: "(If sensitive data is being inspected apart from the normal usage, the attack belongs to confidential data view.) An insider with authorized access to a system inspects sensitive data outside of the scope of their normal business tasks or without a legitimate purpose. Although the insider may have technical access to confidential information due to their role, viewing this data without operational necessity or approval violates confidentiality principles. This threat typically arises in business processes where sensitive information is exposed but not adequately restricted based on task relevance."

            },
            {
                threat: "Unapproved Confidential Data Transfer",
                description: "(The illegal distribution of confidential files such as password lists, financial information, and other sensitive material is a part of confidential data transfer.)An insider distributes or transmits confidential data—such as financial records, customer information, password lists, or other sensitive files—without following approved data sharing or transfer protocols. This may involve sending data to unauthorized recipients, uploading it to external platforms, or copying it to removable media. Business processes often allow certain data exchanges internally, but this threat occurs when insiders deliberately or negligently bypass these controls, risking the exposure of sensitive information."
            },
            {
                threat: "Unauthorized Access to Confidential Credentials",
                description: "(Attacks in this category happen when an insider gets access to crypto keys and other credentials without authorization).An insider gains access to authentication credentials, such as cryptographic keys, passwords, or tokens, without proper authorization. This threat involves exploiting weaknesses in access management or benefiting from insufficient segregation of duties, allowing insiders to acquire credentials they are not entitled to. In secure business processes, credentials are tightly managed to prevent unauthorized use, and violations like these create a high risk of further unauthorized activities and data breaches."
            }

        ]
    },
    {
        principle: "Integrity",
        threats: [
            {
                threat: "Unauthorized Data Corruption",
                description: "(uption, the fraudulent modification of data can be understood. It happens when information is manipulated within either an application or also a system. Incidents in the past have shown that tampering with cookies is a widely used technique to corrupt data in an unauthorized manner.)An insider deliberately or accidentally modifies, tampers with, or corrupts data within a system or application, leading to the loss of data integrity. This includes unauthorized changes to records, manipulation of cookies, or alteration of transactional data. Business processes expect data to remain accurate and trustworthy, but when insiders exploit their access to manipulate data, it can result in financial loss, process failure, or legal non-compliance."
            },
            {
                threat: "Malicious Code Modification/Injection",
                description: "(de programming small modifications can have a huge impact. Logic bombs, trojan horses, and other malicious code injections are examples of this attack group.)An insider introduces malicious code, such as logic bombs, trojan horses, or unauthorized script modifications, into software components, applications, or process control systems. Even small, targeted code changes can cause major disruptions or create hidden backdoors. Business processes relying on software integrity are highly vulnerable if insiders tamper with source code, scripts, or configuration files in unauthorized ways."
            },
            {
                threat: "Insider-Driven Malware Installation",
                description: "(The installation of malware can originate from various sources. The use or download of illegal software or offensive material has a higher chance of containing trojan horses or trapdoors in order to compromise a computer system.)An insider installs malware—either intentionally or by neglecting security protocols—on company systems. Malware can originate from unofficial software, compromised media, or deliberate download of infected content. Such actions can introduce trojans, backdoors, or trapdoors into business-critical systems, severely compromising the integrity and security of operational processes."
            },
            {
                threat: "Unauthorized System Control Manipulation",
                description: "(When default configurations are being modified or the protection of components gets disabled attackers manipulate system controls.)An insider alters system configurations, disables security mechanisms, or modifies protection settings without proper authorization, thereby weakening the integrity of system controls. This includes changing default settings, deactivating firewalls, or disabling authentication processes. Business processes depend on secure and stable system configurations; unauthorized manipulations expose them to exploitation and operational risk."
            }
        ]
    },
    {
        principle: "Availability",
        threats: [
            {
                threat: "Insider-Driven Hardware Manipulation",
                description: "(All attacks that include hardware are aggregated in this group. Especially when capable of adding or removing components of hardware to harm a computer system.)hardware is defective it can get vulnerable to insider attacks. However, an insider is also An insider deliberately tampers with hardware components, such as removing, damaging, or altering physical devices, leading to system instability or unavailability. Additionally, defective hardware may become an easier target for insider exploitation. Business processes rely on properly functioning hardware to ensure system availability; unauthorized hardware interventions by insiders directly compromise this availability and can lead to service interruptions or data loss."
            },
            {
                threat: "System Resource Exhaustion Attack",
                description: "(In resource exhaustion attacks, the availability of the system is being compromised. Examples that belong to this category are DoS, buffer overflow, and replay attacks.)An insider intentionally depletes system resources such as memory, processing power, or storage capacity to make systems or applications unavailable. This can involve techniques like Denial-of-Service (DoS), buffer overflows, or replay attacks. Business processes expecting continuous system availability are disrupted when insiders overload resources, causing system slowdowns or outages."
            },
            {
                threat: "Network Resource Exhaustion Attack",
                description: "(Unlike resource exhaustion attacks, not the system but the network is not available because of an overload. This can happen when a large amount of data is being downloaded in a small time frame such that the network is not able to process other packets.)An insider deliberately overloads network infrastructure by generating excessive data traffic, leading to degraded or unavailable network services. For example, initiating large-scale downloads or flooding the network with packets can prevent legitimate communications from succeeding. Processes that depend on reliable network connectivity suffer significant operational disruptions under such insider-driven network exhaustion attacks."
            },
            {
                threat: "Unauthorized Data Deletion",
                description: "(The loss of data because of its destruction by an insider is labeled as data deletion.)An insider intentionally deletes essential data, leading to its permanent loss or temporary unavailability. This includes deleting files, records, or database entries critical to business operations. While some roles may have legitimate deletion permissions, this threat involves unauthorized, malicious, or negligent deletion, directly impacting process continuity and data availability."
            }
        ]
    },
    {
        principle: "Accountability",
        threats: [
            {
                threat: "System Control Circumvention by Insiders",
                description: "(There are various ways in which system controls can be circumvented. In the sources, the altering or disabling of audit logs has been mentioned most frequently.)An insider bypasses or disables system control mechanisms, such as altering or deleting audit logs, to hide malicious activities or unauthorized actions. Business processes rely on audit trails and system monitoring to ensure accountability and traceability of actions. Circumventing these controls compromises the ability to detect, investigate, or attribute malicious behavior, weakening overall accountability within the organization."
            },
            {
                threat: "Unauthorized Privilege Elevation/Escalation",
                description: "(In case of the modification of user access rights, privileges in a system can be elevated. This gives the user the capability to get unauthorized access to information or systems.)An insider modifies user access rights to gain higher privileges than originally authorized, enabling access to restricted data, systems, or administrative functions. This threat often involves exploiting misconfigurations or weaknesses in access control procedures. Business processes expect that users only operate within their assigned privileges; unauthorized elevation of privileges can lead to further insider threats, such as data theft or system manipulation."
            },
            {
                threat: "Abuse of Legitimate Privileges",
                description: "(Even if users are allowed to access certain data or systems, they can still misuse their privileges to attack an organization. They could for instance abuse an adjustment transaction or error-correction procedures to hide their intrigues.)An insider misuses legitimate access rights to manipulate processes, conceal fraudulent actions, or gain unauthorized benefits. Even when access to data, transactions, or system functions is formally permitted, insiders may intentionally abuse error correction procedures, adjustment transactions, or process loopholes to cause harm or hide malicious activities. Business processes assume that authorized actions are performed in good faith, making this type of insider threat particularly difficult to detect without additional controls."
            }
        ]
    },
    {
        principle: "Authenticity",
        threats: [
            {
                threat: "Insider-Driven Social Engineering Attack",
                description: "(Attack vectors in social engineering that were found in the context of insider threats are tailgaiting, ingratiation, phishing, pretexting, and baiting. These techniques are applied to deceive an employee in order to gain unauthorized access.)An insider leverages social engineering techniques—such as tailgating, ingratiation, phishing, pretexting, or baiting—to manipulate employees into granting unauthorized access to systems, data, or physical areas. These attacks exploit human trust and process weaknesses rather than technical vulnerabilities. Business processes typically rely on the authenticity of interactions and employee awareness; social engineering undermines these assumptions by deceiving staff into bypassing security controls."
            },
            {
                threat: "Insider Impersonation Attack",
                description: "(Masquerading as an employee of an enterprise is a typical impersonation attack in insider threats.)An insider pretends to be another employee, contractor, or trusted party within the organization to gain unauthorized access to systems, resources, or sensitive information. This can involve the use of stolen credentials, forged identification, or deceptive communications. Business processes that depend on accurate identity verification are particularly vulnerable when insiders impersonate legitimate users to bypass access restrictions."
            },
            {
                threat: "Insider-Facilitated Man-in-the-Middle Attack",
                description: "(When attackers place themselves in between a client and a server and intercept all the messages that are sent between those two parties, they are called man in the middle.)An insider positions themselves between two communicating parties, such as a client and a server, intercepting, altering, or eavesdropping on transmitted information without the knowledge of the involved users. This may occur in network communications, internal system interfaces, or application-level data exchanges. Business processes that rely on the authenticity and confidentiality of communication channels are compromised when insiders conduct or enable such man-in-the-middle attacks."
            }
        ]
    },
]