import {SecurityPrinciples} from "./securityPrinciples";
import {InsiderThreatGroups} from "./insiderThreatGroups";
import {BpmnElements} from "./bpmnElements";

export const database = [
    {
        principle: SecurityPrinciples.confidentiality,
        threats: [
            {
                threat: InsiderThreatGroups.confidentialDataAcquisition,
                elements: [BpmnElements.dataObject, BpmnElements.dataStore],
                description: "Data that is being stolen or used inappropriately its in this category. The attack can target not only a computer system but also a web service when for instance a session is being hijacked.",
            },
            {
                threat: InsiderThreatGroups.confidentialDataView,
                elements: [BpmnElements.dataObject, BpmnElements.dataStore, BpmnElements.receiveTask, BpmnElements.intermediateCatchEvent, BpmnElements.startEvent],
                description: "If sensitive data is being inspected apart from the normal usage, the attack belongs to confidential data view."

            },
            {
                threat: InsiderThreatGroups.confidentialDataTransfer,
                elements: [BpmnElements.dataObject, BpmnElements.sendTask, BpmnElements.messageEventDefinition],
                description: "The illegal distribution of confidential files such as password lists, financial information, and other sensitive material is a part of confidential data transfer."
            },
            {
                threat: InsiderThreatGroups.unauthorizedAccessToCredentials,
                elements: [BpmnElements.dataObject, BpmnElements.dataStore],
                description: "Attacks in this category happen when an insider gets access to crypto keys and other credentials without authorization"
            }

        ]
    },
    {
        principle: SecurityPrinciples.integrity,
        threats: [
            {
                threat: InsiderThreatGroups.dataCorruption,
                elements: [BpmnElements.manualTask, BpmnElements.userTask, BpmnElements.serviceTask, BpmnElements.dataObject, BpmnElements.dataStore, BpmnElements.sendTask, BpmnElements.messageEventDefinition],
                description: "With data corruption, the fraudulent modification of data can be understood. It happens when information is manipulated within either an application or also a system. Incidents in the past have shown that tampering with cookies is a widely used technique to corrupt data in an unauthorized manner."
            },
            {
                threat: InsiderThreatGroups.maliciousCodeModification,
                elements: [BpmnElements.serviceTask],
                description: "In software code programming small modifications can have a huge impact. Logic bombs, trojan horses, and other malicious code injections are examples of this attack group."
            },
            {
                threat: InsiderThreatGroups.malwareInstallation,
                elements: [BpmnElements.dataObject, BpmnElements.receiveTask, BpmnElements.sendTask, BpmnElements.intermediateCatchEvent, BpmnElements.startEvent, BpmnElements.messageEventDefinition],
                description: "The installation of malware can originate from various sources. The use or download of illegal software or offensive material has a higher chance of containing trojan horses or trapdoors in order to compromise a computer system."
            },
            {
                threat: InsiderThreatGroups.systemControlManipulation,
                elements: [BpmnElements.userTask],
                description: "When default configurations are being modified or the protection of components gets disabled attackers manipulate system controls."
            }
        ]
    },
    {
        principle: SecurityPrinciples.availability,
        threats: [
            {
                threat: InsiderThreatGroups.hardwareAttack,
                elements: [BpmnElements.manualTask],
                description: "All attacks that include hardware are aggregated in this group. Especially when hardware is defective it can get vulnerable to insider attacks. However, an insider is also capable of adding or removing components of hardware to harm a computer system."
            },
            {
                threat: InsiderThreatGroups.resourceExhaustionAttack,
                elements: [BpmnElements.serviceTask],
                description: "In resource exhaustion attacks, the availability of the system is being compromised. Examples that belong to this category are DoS, buffer overflow, and replay attacks."
            },
            {
                threat: InsiderThreatGroups.networkExhaustionAttack,
                elements: [BpmnElements.serviceTask, BpmnElements.dataObject, BpmnElements.sendTask, BpmnElements.messageEventDefinition],
                description: "Unlike resource exhaustion attacks, not the system but the network is not available because of an overload. This can happen when a large amount of data is being downloaded in a small time frame such that the network is not able to process other packets."
            },
            {
                threat: InsiderThreatGroups.dataDeletion,
                elements: [BpmnElements.userTask, BpmnElements.serviceTask, BpmnElements.dataObject, BpmnElements.dataStore],
                description: "The loss of data because of its destruction by an insider is labeled as data deletion."
            }
        ]
    },
    {
        principle: SecurityPrinciples.accountability,
        threats: [
            {
                threat: InsiderThreatGroups.systemControlCircumvention,
                elements: [BpmnElements.userTask],
                description: "There are various ways in which system controls can be circumvented. In the sources, the altering or disabling of audit logs has been mentioned most frequently."
            },
            {
                threat: InsiderThreatGroups.unauthorizedPrivilegeElevation,
                elements: [BpmnElements.manualTask, BpmnElements.userTask],
                description: "In case of the modification of user access rights, privileges in a system can be elevated. This gives the user the capability to get unauthorized access to information or systems."
            },
            {
                threat: InsiderThreatGroups.misuseOfPrivileges,
                elements: [BpmnElements.userTask],
                description: " Even if users are allowed to access certain data or systems, they can still misuse their privileges to attack an organization. They could for instance abuse an adjustment transaction or error-correction procedures to hide their intrigues."
            }
        ]
    },
    {
        principle: SecurityPrinciples.authenticity,
        threats: [
            {
                threat: InsiderThreatGroups.socialEngineeringAttack,
                elements: [BpmnElements.sendTask],
                description: "Attack vectors in social engineering that were found in the context of insider threats are tailgaiting, ingratiation, phishing, pretexting, and baiting. These techniques are applied to deceive an employee in order to gain unauthorized access."
            },
            {
                threat: InsiderThreatGroups.impersonationAttack,
                elements: [BpmnElements.userTask, BpmnElements.receiveTask, BpmnElements.sendTask, BpmnElements.intermediateCatchEvent, BpmnElements.startEvent, BpmnElements.messageEventDefinition],
                description: "Masquerading as an employee of an enterprise is a typical impersonation attack in insider threats."
            },
            {
                threat: InsiderThreatGroups.manInTheMiddleAttack,
                elements: [BpmnElements.receiveTask, BpmnElements.sendTask, BpmnElements.intermediateCatchEvent, BpmnElements.startEvent, BpmnElements.messageEventDefinition],
                description: "When attackers place themselves in between a client and a server and intercept all the messages that are sent between those two parties, they are called man in the middle."
            }
        ]
    },
]