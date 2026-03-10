export const knowledgeBaseLLM = [
    {
        principle: "Confidentiality",
        threats: [
            {
                threat: "Confidential Data Acquisition",
                description: "Data that is being stolen or used inappropriately its in this category. The attack can target not only a computer system but also a web service when for instance a session is being hijacked."
            },
            {
                threat: "Confidential Data View",
                description: "If sensitive data is being inspected apart from the normal usage, the attack belongs to confidential data view."

            },
            {
                threat: "Confidential Data Transfer",
                description: "The illegal distribution of confidential files such as password lists, financial information, and other sensitive material is a part of confidential data transfer."
            },
            {
                threat: "Unauthorized Access To Credentials",
                description: "Attacks in this category happen when an insider gets access to crypto keys and other credentials without authorization."
            }

        ]
    },
    {
        principle: "Integrity",
        threats: [
            {
                threat: "Data Corruption",
                description: "With data corruption, the fraudulent modification of data can be understood. It happens when information is manipulated within either an application or also a system. Incidents in the past have shown that tampering with cookies is a widely used technique to corrupt data in an unauthorized manner."
            },
            {
                threat: "Malicious Code Modification",
                description: "In software code programming small modifications can have a huge impact. Logic bombs, trojan horses, and other malicious code injections are examples of this attack group."
            },
            {
                threat: "Malware Installation",
                description: "The installation of malware can originate from various sources. The use or download of illegal software or offensive material has a higher chance of containing trojan horses or trapdoors in order to compromise a computer system."
            },
            {
                threat: "System Control Manipulation",
                description: "When default configurations are being modified or the protection of components gets disabled attackers manipulate system controls."
            }
        ]
    },
    {
        principle: "Availability",
        threats: [
            {
                threat: "Hardware Attack",
                description: "All attacks that include hardware are aggregated in this group. Especially when hardware is defective it can get vulnerable to insider attacks. However, an insider is also capable of adding or removing components of hardware to harm a computer system."
            },
            {
                threat: "Resource Exhaustion Attack",
                description: "In resource exhaustion attacks, the availability of the system is being compromised. Examples that belong to this category are DoS, buffer overflow, and replay attacks."
            },
            {
                threat: "Network Exhaustion Attack",
                description: "Unlike resource exhaustion attacks, not the system but the network is not available because of an overload. This can happen when a large amount of data is being downloaded in a small time frame such that the network is not able to process other packets."
            },
            {
                threat: "Data Deletion",
                description: "The loss of data because of its destruction by an insider is labeled as data deletion."
            }
        ]
    },
    {
        principle: "Accountability",
        threats: [
            {
                threat: "System Control Circumvention",
                description: "There are various ways in which system controls can be circumvented. In the sources, the altering or disabling of audit logs has been mentioned most frequently."
            },
            {
                threat: "Unauthorized Privilege Elevation",
                description: "In case of the modification of user access rights, privileges in a system can be elevated. This gives the user the capability to get unauthorized access to information or systems."
            },
            {
                threat: "Misuse Of Privileges",
                description: "Even if users are allowed to access certain data or systems, they can still misuse their privileges to attack an organization. They could for instance abuse an adjustment transaction or error-correction procedures to hide their intrigues."
            }
        ]
    },
    {
        principle: "Authenticity",
        threats: [
            {
                threat: "Social Engineering Attack",
                description: "Attack vectors in social engineering that were found in the context of insider threats are tailgaiting, ingratiation, phishing, pretexting, and baiting. These techniques are applied to deceive an employee in order to gain unauthorized access."
            },
            {
                threat: "Impersonation Attack",
                description: "Masquerading as an employee of an enterprise is a typical impersonation attack in insider threats."
            },
            {
                threat: "Man In The Middle Attack",
                description: "When attackers place themselves in between a client and a server and intercept all the messages that are sent between those two parties, they are called man in the middle."
            }
        ]
    },
]