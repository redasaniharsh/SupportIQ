#!/usr/bin/env python3
"""Creates >=10 realistic, detailed knowledge articles per DESIGN.md 5.3 and
writes them to Mongo `knowledge_articles`. Idempotent — reruns upsert by
article_id rather than duplicating.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.db import collections as c  # noqa: E402
from app.db.indexes import create_indexes  # noqa: E402
from app.db.mongo import mongo_manager  # noqa: E402
from app.utils.dates import utcnow  # noqa: E402

logger = get_logger(__name__)

ARTICLES = [
    {
        "article_id": "KB-001",
        "title": "Multi-Factor Authentication (MFA) Enrollment and Login Failures",
        "category": "Access Management",
        "service": "identity",
        "symptoms": [
            "User cannot complete MFA enrollment during first login",
            "Authenticator app push notification never arrives",
            "\"Invalid code\" error even when entering the correct TOTP code",
            "User lost their phone and cannot receive MFA prompts",
        ],
        "root_causes": [
            "Device clock drift causing TOTP codes to fall outside the valid time window",
            "User enrolled a personal device that was later wiped or replaced",
            "Push notifications blocked by corporate MDM policy or a firewall on the mobile carrier side",
            "Account was provisioned with MFA required before the user completed enrollment, locking them out",
        ],
        "troubleshooting_steps": [
            "Confirm the user's identity via an alternate verification method (manager confirmation + employee ID) before touching MFA settings.",
            "Check the identity provider's admin console for the user's MFA enrollment status and last successful auth timestamp.",
            "Ask the user to verify their device's date/time is set to automatic (not manual) to rule out clock drift.",
            "If the authenticator app is unreachable, issue a temporary bypass code valid for a single login and force re-enrollment on next login.",
            "If the device was lost or wiped, remove the old MFA device binding from the identity provider and have the user re-enroll a new device.",
            "For push-notification failures, confirm the mobile device has data/Wi-Fi connectivity and that the authenticator app is not battery-optimized into a suspended state.",
        ],
        "resolution": (
            "Verify identity out-of-band, remove the stale MFA device binding in the identity provider, "
            "issue a single-use temporary bypass code, and have the user re-enroll a new authenticator device. "
            "Confirm successful login before closing the ticket."
        ),
        "escalation_conditions": [
            "User cannot be verified through any out-of-band method — escalate to Security team for identity verification.",
            "Identity provider itself is returning 5xx errors for MFA enrollment across multiple users — escalate to Infrastructure/IAM on-call.",
        ],
        "tags": ["mfa", "authentication", "login", "identity", "2fa", "totp"],
    },
    {
        "article_id": "KB-002",
        "title": "Self-Service and Helpdesk-Assisted Password Reset",
        "category": "Access Management",
        "service": "identity",
        "symptoms": [
            "User forgot their domain/network password",
            "Password reset link expired or was never received",
            "\"Your password does not meet complexity requirements\" on reset",
            "Password reset succeeds but user still cannot log into VPN or email",
        ],
        "root_causes": [
            "Password reset email routed to spam or blocked by an email filter rule",
            "Password policy requires characters/length the user's proposed password does not meet",
            "Cached credentials on the endpoint (Windows Credential Manager) were not updated after the reset, causing repeated auth failures",
            "Reset was performed on the wrong identity (e.g. personal vs. corporate account) due to similar usernames",
        ],
        "troubleshooting_steps": [
            "Confirm the exact username/UPN being reset and check for lookalike accounts.",
            "If the reset email did not arrive, check spam/junk folders and confirm the registered recovery email is current.",
            "Walk the user through the organization's password complexity rules (length, character classes, reuse history) before they submit a new password.",
            "After a successful reset, instruct the user to clear cached credentials (Windows Credential Manager / macOS Keychain) for the affected service and restart the client application.",
            "If VPN or email still fails after a confirmed reset, check for account lockout status separately (see KB-003) — a reset does not automatically clear a lockout counter on some identity providers.",
        ],
        "resolution": (
            "Reset the password through the identity provider's admin console, confirm it meets the current "
            "complexity policy, and have the user clear cached credentials on all active devices before "
            "attempting to log into downstream services."
        ),
        "escalation_conditions": [
            "Reset succeeds in the identity provider but downstream services (VPN, email) continue to reject the new password after cache clearing — escalate to Identity/SSO team to check federation sync lag.",
        ],
        "tags": ["password", "reset", "identity", "sso", "credentials"],
    },
    {
        "article_id": "KB-003",
        "title": "Account Lockout Diagnosis and Recovery",
        "category": "Access Management",
        "service": "identity",
        "symptoms": [
            "\"Your account has been locked due to too many failed sign-in attempts\"",
            "User is repeatedly locked out shortly after each unlock",
            "Lockout occurs at a specific time of day, correlating with a scheduled task or old device",
        ],
        "root_causes": [
            "A saved credential on an old device, mapped drive, or scheduled task is repeatedly retrying with a stale password",
            "Mobile device mail profile still has the old password cached and is retrying continuously",
            "Genuine brute-force attempt against the account from an external IP",
        ],
        "troubleshooting_steps": [
            "Check the identity provider's sign-in logs for the source of the failed attempts (device name, IP, application).",
            "If failures originate from a known device/app with a stale credential, have the user update or remove that saved credential (Credential Manager, mail profile, mapped network drive).",
            "If failures originate from an unrecognized external IP or unfamiliar location, treat as a possible compromise: unlock the account, force a password reset, and open a security review.",
            "Unlock the account in the identity provider and monitor sign-in logs for 15–30 minutes after unlock to confirm the repeated failures have stopped.",
        ],
        "resolution": (
            "Identify and remediate the source of the repeated failed authentication attempts (stale cached "
            "credential or external actor), unlock the account, and confirm no further failures occur post-unlock."
        ),
        "escalation_conditions": [
            "Failed attempts originate from an unrecognized external IP/location — escalate immediately to the Security team as a possible account compromise.",
        ],
        "tags": ["account lockout", "identity", "security", "authentication"],
    },
    {
        "article_id": "KB-004",
        "title": "Laptop Fails to Boot or Boots into Recovery Mode",
        "category": "Laptop/Endpoint",
        "service": "endpoint",
        "symptoms": [
            "Laptop is stuck at manufacturer logo and never reaches the OS login screen",
            "Device automatically boots into Windows Recovery Environment (WinRE) or macOS Recovery",
            "Blue/black screen with a stop code immediately after a recent update",
        ],
        "root_causes": [
            "A failed or interrupted OS/firmware update left the boot partition in an inconsistent state",
            "Disk corruption on the system volume, often following an unclean shutdown",
            "Third-party full-disk encryption or a security agent conflicting with the boot loader after an update",
        ],
        "troubleshooting_steps": [
            "Note the exact stop code / error message shown on screen — this determines the fix path.",
            "Attempt a safe-mode boot (Windows) or booting while holding the recovery key combo (macOS) to isolate whether a driver/startup item is at fault.",
            "If in recovery mode, run built-in startup repair / disk-check tools before attempting a reinstall.",
            "Check whether a patch or endpoint-security update was pushed to this device in the last 24-48 hours; if so, check the vendor's known-issues bulletin.",
            "If data on the drive is confirmed backed up (via the endpoint backup agent), attempt an in-place OS repair before considering a full reimage.",
        ],
        "resolution": (
            "Run startup repair from the recovery environment; if that fails, perform an in-place OS repair "
            "preserving user data (confirmed backed up first), or escalate for a full reimage if corruption is severe."
        ),
        "escalation_conditions": [
            "Disk-check tools report physical/hardware disk errors — escalate to hardware depot for disk replacement.",
            "Multiple devices in the fleet show the same symptom after a single patch — escalate to Endpoint Engineering to pause the rollout.",
        ],
        "tags": ["laptop", "boot failure", "endpoint", "recovery mode", "bsod"],
    },
    {
        "article_id": "KB-005",
        "title": "Laptop Battery Draining Abnormally Fast or Not Charging",
        "category": "Laptop/Endpoint",
        "service": "endpoint",
        "symptoms": [
            "Battery percentage drops rapidly even when the laptop is idle or asleep",
            "Laptop shows \"plugged in, not charging\"",
            "Battery health indicator reports significantly reduced capacity",
        ],
        "root_causes": [
            "A background process or driver is preventing the device from entering low-power sleep states",
            "Faulty charger, dock, or USB-C cable not delivering sufficient wattage",
            "Battery has genuinely degraded past its usable cycle count (common after 2+ years of daily use)",
        ],
        "troubleshooting_steps": [
            "Check the OS power/battery report (e.g. `powercfg /batteryreport` on Windows) for design capacity vs. current full-charge capacity.",
            "Identify processes preventing sleep using the OS's power diagnostic tools; update or remove the offending driver/app.",
            "Swap the charger/cable/dock with a known-good spare to rule out a hardware fault in the charging path.",
            "If the battery report shows capacity below ~70-80% of design capacity, treat as end-of-life hardware.",
        ],
        "resolution": (
            "If a charger/cable/dock is at fault, replace it. If the battery health report shows significant "
            "degradation, submit a hardware depot request for battery replacement; provide the battery report as evidence."
        ),
        "escalation_conditions": [
            "Device is under active warranty and shows swelling or physical deformation of the battery — escalate immediately as a safety issue and stop using the device.",
        ],
        "tags": ["laptop", "battery", "endpoint", "hardware", "charging"],
    },
    {
        "article_id": "KB-006",
        "title": "VPN Connection Fails or Drops Repeatedly",
        "category": "Network & VPN",
        "service": "network",
        "symptoms": [
            "VPN client shows \"unable to establish a connection\" or times out",
            "VPN connects but drops every few minutes",
            "VPN connects but internal resources (file shares, internal sites) are unreachable",
            "VPN failure started immediately after a password reset",
        ],
        "root_causes": [
            "Cached VPN credentials were not updated after a recent password reset",
            "Split-tunnel/routing misconfiguration on the client profile after a network policy change",
            "Local network (home Wi-Fi/router) is blocking the VPN protocol's UDP/TCP port",
            "VPN concentrator/gateway capacity issue or scheduled maintenance affecting a region",
        ],
        "troubleshooting_steps": [
            "Confirm whether the failure started right after a recent password reset; if so, have the user re-enter credentials in the VPN client rather than relying on a saved/cached credential.",
            "Check the VPN gateway's status page/dashboard for regional outages or maintenance windows.",
            "Have the user try a different network (mobile hotspot) to rule out local ISP/router port blocking.",
            "Verify the client's VPN profile/config version matches the current server-side policy; push an updated profile if it is stale.",
            "For repeated drops, check the client log for renegotiation/keepalive failures and adjust the MTU or keepalive interval per vendor guidance.",
        ],
        "resolution": (
            "Re-authenticate with the current credentials, confirm/refresh the VPN client profile, and validate "
            "connectivity from an alternate network to isolate client vs. gateway issues before closing."
        ),
        "escalation_conditions": [
            "Multiple users in the same region report simultaneous VPN failures — escalate to Network Operations to check gateway health.",
            "Connectivity works on an alternate network but never on the user's home network — escalate to the user's ISP or provide a documented port-forwarding workaround.",
        ],
        "tags": ["vpn", "network", "connectivity", "remote access"],
    },
    {
        "article_id": "KB-007",
        "title": "Outlook / Exchange Mailbox Sync and Send/Receive Failures",
        "category": "Email & Collaboration",
        "service": "email",
        "symptoms": [
            "Outlook shows \"disconnected\" or stuck at \"trying to connect\"",
            "Emails stay in the Outbox and never send",
            "Mailbox missing recent emails that are visible in Outlook Web Access (OWA)",
            "Shared mailbox or delegated calendar suddenly inaccessible",
        ],
        "root_causes": [
            "Corrupted local OST cache file out of sync with the server",
            "Expired or revoked modern-auth token after an MFA/device compliance policy change",
            "Mailbox has exceeded its storage quota, blocking send",
            "Conditional access policy blocking the client due to an out-of-compliance device",
        ],
        "troubleshooting_steps": [
            "Confirm the issue also reproduces (or not) in OWA — if OWA works fine, the issue is client-side (Outlook/OST), not the mailbox itself.",
            "Check mailbox size/quota in the admin console; if near/at quota, archive or delete large items.",
            "Have the user sign out and back into Outlook to refresh the modern-auth token; check device compliance status if conditional access is enforced.",
            "If OST corruption is suspected, close Outlook, rename/remove the local OST file, and let Outlook rebuild it on next launch (warn the user this can take time on large mailboxes).",
            "For shared mailbox access loss, verify delegate/full-access permissions were not removed in a recent access review.",
        ],
        "resolution": (
            "Isolate client vs. server issue via OWA, then resolve the specific cause: rebuild the OST cache, "
            "free mailbox quota, refresh authentication, or restore delegate permissions as applicable."
        ),
        "escalation_conditions": [
            "OWA also fails for the same mailbox — escalate to Messaging/Exchange admins to check mailbox database health.",
            "Conditional access is blocking many devices fleet-wide after a policy change — escalate to Identity team to review the new policy.",
        ],
        "tags": ["outlook", "exchange", "email", "sync", "collaboration"],
    },
    {
        "article_id": "KB-008",
        "title": "Microsoft Teams / Collaboration Tool Call Quality and Screen-Share Issues",
        "category": "Email & Collaboration",
        "service": "collaboration",
        "symptoms": [
            "Audio cutting out or garbled during calls",
            "Screen share shows a black/frozen frame to other participants",
            "Video freezes while audio continues",
        ],
        "root_causes": [
            "Insufficient upload bandwidth or high jitter on the user's network",
            "Hardware acceleration conflict between the collaboration client and the GPU driver",
            "Corporate VPN routing all media traffic through a distant gateway instead of allowing local breakout",
        ],
        "troubleshooting_steps": [
            "Run the collaboration tool's built-in network/call-quality diagnostics to capture jitter, packet loss, and round-trip time.",
            "If on VPN, check whether the client/network policy exempts (split-tunnels) real-time media traffic from the tunnel; enable if supported and permitted by security policy.",
            "Toggle hardware acceleration off in the collaboration client to rule out a GPU driver conflict, especially after a recent GPU driver update.",
            "Test from a wired connection or different network to isolate a local Wi-Fi issue.",
        ],
        "resolution": (
            "Identify whether the bottleneck is network (bandwidth/jitter/VPN routing) or client-side (hardware "
            "acceleration/driver) using built-in diagnostics, then apply the matching fix — split-tunnel media "
            "traffic, disable hardware acceleration, or recommend a wired connection."
        ),
        "escalation_conditions": [
            "Call quality diagnostics show high packet loss even on a wired, non-VPN connection — escalate to Network team to check the office's uplink/QoS configuration.",
        ],
        "tags": ["teams", "collaboration", "video call", "network", "screen share"],
    },
    {
        "article_id": "KB-009",
        "title": "ERP/WMS Order or Inventory Sync Discrepancy",
        "category": "ERP/WMS",
        "service": "erp",
        "symptoms": [
            "Inventory count in the WMS does not match the ERP system",
            "Orders stuck in \"pending sync\" status between ERP and WMS",
            "Duplicate orders or duplicate inventory adjustments appear after a sync retry",
        ],
        "root_causes": [
            "Integration/middleware queue backlog or a failed batch job between ERP and WMS",
            "A manual inventory adjustment was made directly in the WMS without going through the ERP-approved workflow, causing drift",
            "Sync job was retried without idempotency checks after a timeout, causing duplicate records",
        ],
        "troubleshooting_steps": [
            "Check the integration/middleware job dashboard for failed or stuck sync batches around the time discrepancy began.",
            "Compare the specific SKU/order IDs in both systems to identify whether the discrepancy is a timing lag (will self-correct on next sync) or a genuine data mismatch.",
            "If a manual WMS adjustment bypassed the ERP workflow, document it and re-run the reconciliation job so ERP reflects the true on-hand count.",
            "For duplicate records from a retried sync, identify the duplicate keys and cancel/void the extra records per the finance/inventory team's correction procedure — never delete financial records directly in the database.",
        ],
        "resolution": (
            "Identify the specific failed sync batch or manual bypass causing drift, correct the source data "
            "following the inventory correction procedure, and re-run reconciliation to confirm ERP and WMS agree."
        ),
        "escalation_conditions": [
            "Discrepancy affects financial reporting (e.g. cost-of-goods figures) — escalate to Finance Systems team before making any corrective adjustment.",
            "Integration middleware itself is down or erroring for all sync jobs — escalate to Integration/Platform engineering.",
        ],
        "tags": ["erp", "wms", "inventory", "sync", "integration"],
    },
    {
        "article_id": "KB-010",
        "title": "Network Printer Not Found, Offline, or Print Jobs Stuck in Queue",
        "category": "Printers & Devices",
        "service": "print",
        "symptoms": [
            "Printer shows \"offline\" on the workstation despite being powered on",
            "Print jobs sit in the queue and never complete",
            "New printer cannot be discovered/added on the network",
        ],
        "root_causes": [
            "Printer's static/reserved IP changed (e.g. after a DHCP lease renewal or network change) and the workstation's driver still points to the old IP",
            "Print spooler service on the workstation or print server is hung",
            "Printer's network port/VLAN is unreachable due to a switch or firewall change",
        ],
        "troubleshooting_steps": [
            "Confirm the printer's current IP/hostname from its control panel and compare against the configured port on the workstation/print server.",
            "Restart the Print Spooler service on the affected workstation (and print server, if centrally managed) to clear a hung queue.",
            "Ping the printer's IP from the affected workstation and from the print server to isolate whether the issue is workstation-local or network-wide.",
            "If the printer's IP changed, update the printer port configuration (or re-add the printer) rather than only restarting the spooler.",
            "For new printer discovery failures, confirm the printer and workstation are on the same VLAN/subnet or that appropriate routing/firewall rules allow discovery traffic.",
        ],
        "resolution": (
            "Restart the spooler to clear stuck jobs, then correct the underlying cause — typically an IP/port "
            "mismatch after a network change — and confirm a successful test print before closing."
        ),
        "escalation_conditions": [
            "Ping fails from the print server as well as all workstations — escalate to Network team to check switch port/VLAN status for the printer.",
        ],
        "tags": ["printer", "print queue", "network", "devices"],
    },
    {
        "article_id": "KB-011",
        "title": "Phishing Report and Suspicious Email Handling",
        "category": "Security",
        "service": "security",
        "symptoms": [
            "User reports receiving a suspicious email requesting credentials or payment",
            "User clicked a link in an email and is unsure if their account is compromised",
            "Multiple users report receiving the same suspicious email",
        ],
        "root_causes": [
            "Targeted or bulk phishing campaign bypassing existing email filters",
            "Compromised external vendor/partner account sending phishing emails from a trusted-looking address",
        ],
        "troubleshooting_steps": [
            "Do not click any links or open attachments in the reported email. Use the mail client's \"report phishing\" feature if available, or forward as an attachment to the security mailbox.",
            "Check whether the sender domain/IP has already been flagged in the email security gateway's recent block list.",
            "If the user clicked a link and entered credentials, immediately force a password reset and review recent sign-in activity for that account (see KB-003 for lockout/sign-in log review).",
            "Search the mail environment for other recipients of the same sender/subject to scope the campaign, and quarantine/purge matching messages.",
            "Add the sender domain/IP and any observed indicators (URLs, attachment hashes) to the email security gateway's block list.",
        ],
        "resolution": (
            "Quarantine and purge the phishing email across all recipient mailboxes, block the sender's "
            "domain/IP/URL indicators at the gateway, and force credential reset plus sign-in review for any "
            "user who entered credentials."
        ),
        "escalation_conditions": [
            "Any user confirms they entered credentials or the email requested a wire transfer/payment — escalate immediately to the Security Incident Response team.",
        ],
        "tags": ["phishing", "security", "email", "incident response"],
    },
    {
        "article_id": "KB-012",
        "title": "Desk Phone / Softphone Registration and Call Quality Issues",
        "category": "Telephony",
        "service": "telephony",
        "symptoms": [
            "Desk phone or softphone shows \"unregistered\" and cannot make/receive calls",
            "Calls connect but have one-way audio or significant delay",
            "Voicemail-to-email is not arriving",
        ],
        "root_causes": [
            "SIP registration credentials expired or the phone lost its DHCP-assigned VLAN (voice VLAN) tag",
            "One-way audio typically indicates a NAT/firewall traversal issue for RTP media streams",
            "Voicemail-to-email transcription/forwarding rule was disabled during a recent mailbox migration",
        ],
        "troubleshooting_steps": [
            "Confirm the phone/softphone is on the correct voice VLAN and has a valid IP; reboot the physical handset to force re-registration if needed.",
            "Check the SIP trunk/PBX admin console for the extension's registration status and recent registration failures.",
            "For one-way audio, check firewall/NAT rules for the RTP port range used by the PBX; this is rarely a phone hardware fault.",
            "For missing voicemail-to-email, verify the forwarding rule/integration is still enabled for that mailbox after any recent migration.",
        ],
        "resolution": (
            "Restore correct VLAN/registration for the device, resolve the RTP NAT traversal path for one-way "
            "audio cases, and re-enable voicemail-to-email forwarding for the affected mailbox."
        ),
        "escalation_conditions": [
            "Multiple extensions across a site show registration failures simultaneously — escalate to Telephony/Network on-call to check the PBX/SIP trunk and voice VLAN infrastructure.",
        ],
        "tags": ["telephony", "voip", "sip", "phone", "voicemail"],
    },
    {
        "article_id": "KB-013",
        "title": "Shared Drive / SharePoint File Access Permission Errors",
        "category": "Access Management",
        "service": "collaboration",
        "symptoms": [
            "\"Access denied\" when opening a shared drive or SharePoint site the user previously accessed",
            "File visible in search results but cannot be opened",
            "Permissions were changed after an access review and a legitimate user lost needed access",
        ],
        "root_causes": [
            "A periodic access review removed a group membership the user still legitimately needs",
            "File/folder-level permission was set to inherit-break individually, diverging from the parent site's group permissions",
            "User's account was moved to a different security group after a team/department change without updating resource ACLs",
        ],
        "troubleshooting_steps": [
            "Confirm the exact resource path and check the current ACL/sharing settings for that specific file or folder, not just the parent site.",
            "Check whether the user's group memberships changed recently (e.g. after an access review or org change) using the identity provider's audit log.",
            "If access was removed as part of a legitimate access review, route the request through the standard access-request/approval workflow rather than manually re-granting.",
            "If the loss of access was an unintended side effect of a permission-inheritance break, restore inheritance or explicitly re-add the correct group.",
        ],
        "resolution": (
            "Restore the correct group membership or explicit permission entry for the resource, following the "
            "standard access-approval workflow when the removal was policy-driven rather than accidental."
        ),
        "escalation_conditions": [
            "The requested access falls outside the user's normal role/entitlement — escalate to the resource owner or the Access Governance team rather than granting directly.",
        ],
        "tags": ["sharepoint", "permissions", "access management", "file share"],
    },
]


async def main() -> None:
    configure_logging("INFO")
    settings = get_settings()
    await mongo_manager.connect(settings)
    db = mongo_manager.db
    await create_indexes(db)

    now = utcnow()
    upserted = 0
    for article in ARTICLES:
        doc = {**article, "version": 1, "updated_at": now}
        result = await db[c.KNOWLEDGE_ARTICLES].update_one(
            {"article_id": article["article_id"]},
            {"$set": doc, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        upserted += 1

    print(f"Upserted {upserted} knowledge articles into '{c.KNOWLEDGE_ARTICLES}'.")
    await mongo_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
