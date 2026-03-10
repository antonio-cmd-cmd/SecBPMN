import lancedb

db = lancedb.connect("./my_lancedb")

# --------------------------------------------------------------

import lancedb
import pandas as pd

db = lancedb.connect("./lancedb1")

# ---------------------------------------------------------------

principle_df = pd.DataFrame([
    {"id": 1, "name": "Confidentiality", "description": "Protect information from unauthorized access."},
    {"id": 2, "name": "Integrity", "description": "Ensure information is accurate and trustworthy."},
    {"id": 3, "name": "Availability", "description": "Ensure information is accessible when needed."},
    {"id": 4, "name": "Accountability", "description": "Ensure actions can be traced to responsible parties."},
    {"id": 5, "name": "Authenticity", "description": "Ensure that information is genuine and from a verified source."},
]),
threat_df = pd.DataFrame([
       
     # Confidentiality
     {
        "ID": 1,
        "principle.ID": 1,
        "name": "Unauthorized Confidential Data Acquisition",
        "description_short": "Data that is being stolen or used inappropriately its in this category. The attack can target not only a computer system but also a web service when for instance a session is being hijacked.",
        "description_long": "An insider intentionally or unintentionally obtains confidential data through unauthorized means, such as stealing sensitive information from computer systems, business applications, or online services. This threat includes cases where session hijacking, credential misuse, or exploiting system vulnerabilities enables the insider to access data that exceeds their authorized usage. Business processes that handle confidential data are expected to ensure that access is strictly controlled and monitored, but this threat undermines confidentiality by bypassing these safeguards.",
        "is_default": 1
    },
    {
        "ID": 2,
        "principle.ID": 1,
        "name": "Inappropriate Confidential Data Viewing",
        "description_short": "If sensitive data is being inspected apart from the normal usage, the attack belongs to confidential data view.",
        "description_long": "An insider with authorized access to a system inspects sensitive data outside of the scope of their normal business tasks or without a legitimate purpose. Although the insider may have technical access to confidential information due to their role, viewing this data without operational necessity or approval violates confidentiality principles. This threat typically arises in business processes where sensitive information is exposed but not adequately restricted based on task relevance.",
        "is_default": 1
    },
    {
        "ID": 3,
        "principle.ID": 1,
        "name": "Unapproved Confidential Data Transfer",
        "description_short": "The illegal distribution of confidential files such as password lists, financial information, and other sensitive material is a part of confidential data transfer.",
        "description_long": "An insider distributes or transmits confidential data—such as financial records, customer information, password lists, or other sensitive files—without following approved data sharing or transfer protocols. This may involve sending data to unauthorized recipients, uploading it to external platforms, or copying it to removable media. Business processes often allow certain data exchanges internally, but this threat occurs when insiders deliberately or negligently bypass these controls, risking the exposure of sensitive information.",
        "is_default": 1
    },
    {
        "ID": 4,
        "principle.ID": 1,
        "name": "Unauthorized Access to Confidential Credentials",
        "description_short": "Attacks in this category happen when an insider gets access to crypto keys and other credentials without authorization.",
        "description_long": "An insider gains access to authentication credentials, such as cryptographic keys, passwords, or tokens, without proper authorization. This threat involves exploiting weaknesses in access management or benefiting from insufficient segregation of duties, allowing insiders to acquire credentials they are not entitled to. In secure business processes, credentials are tightly managed to prevent unauthorized use, and violations like these create a high risk of further unauthorized activities and data breaches.",
        "is_default": 1
    },
    # Integrity
    {
        "ID": 5,
        "principle.ID": 2,
        "name": "Unauthorized Data Corruption",
        "description_short": "uption, the fraudulent modification of data can be understood. It happens when information is manipulated within either an application or also a system. Incidents in the past have shown that tampering with cookies is a widely used technique to corrupt data in an unauthorized manner.",
        "description_long": "An insider deliberately or accidentally modifies, tampers with, or corrupts data within a system or application, leading to the loss of data integrity. This includes unauthorized changes to records, manipulation of cookies, or alteration of transactional data. Business processes expect data to remain accurate and trustworthy, but when insiders exploit their access to manipulate data, it can result in financial loss, process failure, or legal non-compliance.",
        "is_default": 1
    },
    {
        "ID": 6,
        "principle.ID": 2,
        "name": "Malicious Code Modification/Injection",
        "description_short": "de programming small modifications can have a huge impact. Logic bombs, trojan horses, and other malicious code injections are examples of this attack group.",
        "description_long": "An insider introduces malicious code, such as logic bombs, trojan horses, or unauthorized script modifications, into software components, applications, or process control systems. Even small, targeted code changes can cause major disruptions or create hidden backdoors. Business processes relying on software integrity are highly vulnerable if insiders tamper with source code, scripts, or configuration files in unauthorized ways.",
        "is_default": 1
    },
    {
        "ID": 7,
        "principle.ID": 2,
        "name": "Insider-Driven Malware Installation",
        "description_short": "The installation of malware can originate from various sources. The use or download of illegal software or offensive material has a higher chance of containing trojan horses or trapdoors in order to compromise a computer system.",
        "description_long": "An insider installs malware—either intentionally or by neglecting security protocols—on company systems. Malware can originate from unofficial software, compromised media, or deliberate download of infected content. Such actions can introduce trojans, backdoors, or trapdoors into business-critical systems, severely compromising the integrity and security of operational processes.",
        "is_default": 1
    },
    {
        "ID": 8,
        "principle.ID": 2,
        "name": "Unauthorized System Control Manipulation",
        "description_short": "When default configurations are being modified or the protection of components gets disabled attackers manipulate system controls.",
        "description_long": "An insider alters system configurations, disables security mechanisms, or modifies protection settings without proper authorization, thereby weakening the integrity of system controls. This includes changing default settings, deactivating firewalls, or disabling authentication processes. Business processes depend on secure and stable system configurations; unauthorized manipulations expose them to exploitation and operational risk.",
        "is_default": 1
    },

    # Availability (3)
    {
        "ID": 9,
        "principle.ID": 3,
        "name": "Insider-Driven Hardware Manipulation",
        "description_short": "All attacks that include hardware are aggregated in this group. Especially when capable of adding or removing components of hardware to harm a computer system.",
        "description_long": "An insider deliberately tampers with hardware components, such as removing, damaging, or altering physical devices, leading to system instability or unavailability. Additionally, defective hardware may become an easier target for insider exploitation. Business processes rely on properly functioning hardware to ensure system availability; unauthorized hardware interventions by insiders directly compromise this availability and can lead to service interruptions or data loss.",
        "is_default": 1
    },
    {
        "ID": 10,
        "principle.ID": 3,
        "name": "System Resource Exhaustion Attack",
        "description_short": "In resource exhaustion attacks, the availability of the system is being compromised. Examples that belong to this category are DoS, buffer overflow, and replay attacks.",
        "description_long": "An insider intentionally depletes system resources such as memory, processing power, or storage capacity to make systems or applications unavailable. This can involve techniques like Denial-of-Service (DoS), buffer overflows, or replay attacks. Business processes expecting continuous system availability are disrupted when insiders overload resources, causing system slowdowns or outages.",
        "is_default": 1
    },
    {
        "ID": 11,
        "principle.ID": 3,
        "name": "Network Resource Exhaustion Attack",
        "description_short": "Unlike resource exhaustion attacks, not the system but the network is not available because of an overload. This can happen when a large amount of data is being downloaded in a small time frame such that the network is not able to process other packets.",
        "description_long": "An insider deliberately overloads network infrastructure by generating excessive data traffic, leading to degraded or unavailable network services. For example, initiating large-scale downloads or flooding the network with packets can prevent legitimate communications from succeeding. Processes that depend on reliable network connectivity suffer significant operational disruptions under such insider-driven network exhaustion attacks.",
        "is_default": 1
    },
    {
        "ID": 12,
        "principle.ID": 3,
        "name": "Unauthorized Data Deletion",
        "description_short": "The loss of data because of its destruction by an insider is labeled as data deletion.",
        "description_long": "An insider intentionally deletes essential data, leading to its permanent loss or temporary unavailability. This includes deleting files, records, or database entries critical to business operations. While some roles may have legitimate deletion permissions, this threat involves unauthorized, malicious, or negligent deletion, directly impacting process continuity and data availability.",
        "is_default": 1
    },

    # Accountability (4)
    {
        "ID": 13,
        "principle.ID": 4,
        "name": "System Control Circumvention by Insiders",
        "description_short": "There are various ways in which system controls can be circumvented. In the sources, the altering or disabling of audit logs has been mentioned most frequently.",
        "description_long": "An insider bypasses or disables system control mechanisms, such as altering or deleting audit logs, to hide malicious activities or unauthorized actions. Business processes rely on audit trails and system monitoring to ensure accountability and traceability of actions. Circumventing these controls compromises the ability to detect, investigate, or attribute malicious behavior, weakening overall accountability within the organization.",
        "is_default": 1
    },
    {
        "ID": 14,
        "principle.ID": 4,
        "name": "Unauthorized Privilege Elevation/Escalation",
        "description_short": "In case of the modification of user access rights, privileges in a system can be elevated. This gives the user the capability to get unauthorized access to information or systems.",
        "description_long": "An insider modifies user access rights to gain higher privileges than originally authorized, enabling access to restricted data, systems, or administrative functions. This threat often involves exploiting misconfigurations or weaknesses in access control procedures. Business processes expect that users only operate within their assigned privileges; unauthorized elevation of privileges can lead to further insider threats, such as data theft or system manipulation.",
        "is_default": 1
    },
    {
        "ID": 15,
        "principle.ID": 4,
        "name": "Abuse of Legitimate Privileges",
        "description_short": "Even if users are allowed to access certain data or systems, they can still misuse their privileges to attack an organization. They could for instance abuse an adjustment transaction or error-correction procedures to hide their intrigues.",
        "description_long": "An insider misuses legitimate access rights to manipulate processes, conceal fraudulent actions, or gain unauthorized benefits. Even when access to data, transactions, or system functions is formally permitted, insiders may intentionally abuse error correction procedures, adjustment transactions, or process loopholes to cause harm or hide malicious activities. Business processes assume that authorized actions are performed in good faith, making this type of insider threat particularly difficult to detect without additional controls.",
        "is_default": 1
    },

    # Authenticity (5)
    {
        "ID": 16,
        "principle.ID": 5,
        "name": "Insider-Driven Social Engineering Attack",
        "description_short": "Attack vectors in social engineering that were found in the context of insider threats are tailgaiting, ingratiation, phishing, pretexting, and baiting. These techniques are applied to deceive an employee in order to gain unauthorized access.",
        "description_long": "An insider leverages social engineering techniques—such as tailgating, ingratiation, phishing, pretexting, or baiting—to manipulate employees into granting unauthorized access to systems, data, or physical areas. These attacks exploit human trust and process weaknesses rather than technical vulnerabilities. Business processes typically rely on the authenticity of interactions and employee awareness; social engineering undermines these assumptions by deceiving staff into bypassing security controls.",
        "is_default": 1
    },
    {
        "ID": 17,
        "principle.ID": 5,
        "name": "Insider Impersonation Attack",
        "description_short": "Masquerading as an employee of an enterprise is a typical impersonation attack in insider threats.",
        "description_long": "An insider pretends to be another employee, contractor, or trusted party within the organization to gain unauthorized access to systems, resources, or sensitive information. This can involve the use of stolen credentials, forged identification, or deceptive communications. Business processes that depend on accurate identity verification are particularly vulnerable when insiders impersonate legitimate users to bypass access restrictions.",
        "is_default": 1
    },
    {
        "ID": 18,
        "principle.ID": 5,
        "name": "Insider-Facilitated Man-in-the-Middle Attack",
        "description_short": "When attackers place themselves in between a client and a server and intercept all the messages that are sent between those two parties, they are called man in the middle.",
        "description_long": "An insider positions themselves between two communicating parties, such as a client and a server, intercepting, altering, or eavesdropping on transmitted information without the knowledge of the involved users. This may occur in network communications, internal system interfaces, or application-level data exchanges. Business processes that rely on the authenticity and confidentiality of communication channels are compromised when insiders conduct or enable such man-in-the-middle attacks.",
        "is_default": 1
    }
])
print(principle_df.head())
print(threat_df.head())

# ----------------------------------------------------------------
print(type(principle_df))
print(type(threat_df))

db.create_table("principle", principle_df, mode="overwrite")
db.create_table("threat", threat_df, mode="overwrite")