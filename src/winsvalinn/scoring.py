"""Score calculation engine for security and optimization metrics."""

try:
    import psutil
except ImportError:
    psutil = None


class ScoreEngine:
    """Calculates security and optimization scores from scan results."""

    @staticmethod
    def calc_security_score(results):
        score = 100
        recommendations = []

        # Check if third-party AV/security suite is active (affects firewall scoring)
        av_products = results.get("Installed Antivirus", [])
        has_third_party_suite = False
        if isinstance(av_products, list):
            for av in av_products:
                if (
                    isinstance(av, dict)
                    and av.get("enabled")
                    and "defender" not in av.get("name", "").lower()
                    and "windows" not in av.get("name", "").lower()
                ):
                    has_third_party_suite = True
                    break

        # Firewall check (-15 per disabled profile, but skip if third-party manages it)
        fw = results.get("Firewall Status", {})
        if isinstance(fw, dict) and "error" not in fw:
            if not has_third_party_suite:
                for profile in ["domain", "private", "public"]:
                    if fw.get(profile, "").upper() != "ON":
                        score -= 15
                        recommendations.append(
                            {
                                "text": f"Enable firewall for {profile} profile",
                                "severity": "high",
                                "category": "Firewall",
                                "fix": "firewall",
                            }
                        )
            # If third-party suite active, firewall OFF is expected → no penalty
        elif not has_third_party_suite:
            score -= 10
            recommendations.append(
                {
                    "text": "Could not verify firewall status (run as Admin)",
                    "severity": "medium",
                    "category": "Firewall",
                }
            )

        # Defender + third-party AV check
        defender = results.get("Defender Status", {})
        av_products = results.get("Installed Antivirus", [])
        # Check if any third-party AV is active
        has_active_third_party = False
        if isinstance(av_products, list):
            for av in av_products:
                if (
                    isinstance(av, dict)
                    and av.get("enabled")
                    and "defender" not in av.get("name", "").lower()
                    and "windows" not in av.get("name", "").lower()
                ):
                    has_active_third_party = True
                    break

        if isinstance(defender, dict) and "error" not in defender:
            if defender.get("status") != "Enabled" and not has_active_third_party:
                score -= 20
                recommendations.append(
                    {
                        "text": "Enable Windows Defender or install an antivirus",
                        "severity": "high",
                        "category": "Antivirus",
                        "fix": "defender",
                    }
                )
            elif defender.get("status") != "Enabled" and has_active_third_party:
                # Defender off but third-party AV active = OK
                pass
            elif defender.get("real_time") != "Enabled" and not has_active_third_party:
                score -= 10
                recommendations.append(
                    {
                        "text": "Enable Defender real-time protection",
                        "severity": "high",
                        "category": "Antivirus",
                        "fix": "defender",
                    }
                )
        elif not has_active_third_party:
            score -= 15
            recommendations.append(
                {
                    "text": "No active antivirus detected!",
                    "severity": "high",
                    "category": "Antivirus",
                }
            )

        # External ports check (exclude SYSTEM-critical ports from penalty)
        ext_ports = results.get("External Ports", [])
        if isinstance(ext_ports, list):
            # Only count non-system ports as risky
            high_risk_ports = [
                p for p in ext_ports if isinstance(p, dict) and p.get("risk") == "HIGH"
            ]
            non_system_ports = [
                p for p in ext_ports if isinstance(p, dict) and p.get("risk") != "SYSTEM"
            ]
            if high_risk_ports:
                score -= min(15, len(high_risk_ports) * 5)
                recommendations.append(
                    {
                        "text": f"{len(high_risk_ports)} high-risk ports exposed externally",
                        "severity": "high",
                        "category": "Ports",
                    }
                )
            elif len(non_system_ports) > 10:
                score -= 5
                recommendations.append(
                    {
                        "text": f"{len(non_system_ports)} non-system ports exposed externally - review them",
                        "severity": "medium",
                        "category": "Ports",
                    }
                )

        # Suspicious IPs (-5 each, max -20)
        suspicious = results.get("Suspicious IPs", [])
        if suspicious:
            penalty = min(20, len(suspicious) * 5)
            score -= penalty
            recommendations.append(
                {
                    "text": f"Investigate {len(suspicious)} suspicious network connections",
                    "severity": "high",
                    "category": "Network",
                }
            )

        # Suspicious processes (-5 each, max -20)
        procs = results.get("Process Analysis", [])
        high_risk = [p for p in procs if isinstance(p, dict) and p.get("risk") == "HIGH"]
        med_risk = [p for p in procs if isinstance(p, dict) and p.get("risk") == "MEDIUM"]
        if high_risk:
            score -= min(20, len(high_risk) * 8)
            recommendations.append(
                {
                    "text": f"Review {len(high_risk)} high-risk processes",
                    "severity": "high",
                    "category": "Processes",
                }
            )
        if med_risk:
            score -= min(10, len(med_risk) * 3)
            recommendations.append(
                {
                    "text": f"Check {len(med_risk)} medium-risk processes",
                    "severity": "medium",
                    "category": "Processes",
                }
            )

        # ARP spoofing (-10)
        arp = results.get("ARP Table", [])
        spoofing = [e for e in arp if isinstance(e, dict) and e.get("spoofing_risk")]
        if spoofing:
            score -= 10
            recommendations.append(
                {
                    "text": "Potential ARP spoofing detected on network",
                    "severity": "high",
                    "category": "Network",
                }
            )

        # Suspicious scheduled tasks (-3 each, max -12)
        tasks = results.get("Scheduled Tasks", [])
        susp_tasks = [t for t in tasks if isinstance(t, dict) and t.get("suspicious")]
        if susp_tasks:
            score -= min(12, len(susp_tasks) * 3)
            recommendations.append(
                {
                    "text": f"Review {len(susp_tasks)} suspicious scheduled tasks",
                    "severity": "medium",
                    "category": "Tasks",
                }
            )

        # Suspicious DNS entries (-2 each, max -8)
        dns = results.get("DNS Cache", [])
        susp_dns = [d for d in dns if isinstance(d, dict) and d.get("suspicious")]
        if susp_dns:
            score -= min(8, len(susp_dns) * 2)
            recommendations.append(
                {
                    "text": f"Found {len(susp_dns)} suspicious DNS entries",
                    "severity": "low",
                    "category": "DNS",
                    "fix": "dns",
                }
            )

        # Listening services (many = slight risk)
        services = results.get("Listening Services", [])
        if len(services) > 20:
            score -= 5
            recommendations.append(
                {
                    "text": f"{len(services)} services listening - review unnecessary ones",
                    "severity": "low",
                    "category": "Services",
                }
            )

        # Shared resources
        shares = results.get("Shared Resources", [])
        if len(shares) > 3:
            score -= 3
            recommendations.append(
                {
                    "text": f"{len(shares)} shared resources - disable unneeded shares",
                    "severity": "low",
                    "category": "Sharing",
                }
            )

        # Multiple admin accounts
        accounts = results.get("User Accounts", [])
        admins = [a for a in accounts if isinstance(a, dict) and a.get("is_admin")]
        if len(admins) > 2:
            score -= 5
            recommendations.append(
                {
                    "text": f"{len(admins)} admin accounts - reduce admin privileges",
                    "severity": "medium",
                    "category": "Accounts",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "text": "System security looks good! Keep software updated.",
                    "severity": "ok",
                    "category": "General",
                }
            )

        return max(0, min(100, score)), recommendations

    @staticmethod
    def calc_optimization_score(opt_results, sec_results=None):
        score = 100
        recommendations = []

        # RAM usage
        if psutil:
            mem = psutil.virtual_memory()
            if mem.percent > 85:
                score -= 20
                recommendations.append(
                    {
                        "text": "RAM usage critical - close unused apps or upgrade RAM",
                        "severity": "high",
                        "category": "Memory",
                    }
                )
            elif mem.percent > 70:
                score -= 10
                recommendations.append(
                    {
                        "text": "RAM usage high - consider optimizing memory",
                        "severity": "medium",
                        "category": "Memory",
                    }
                )

            # CPU usage
            cpu = psutil.cpu_percent(interval=0.3)
            if cpu > 80:
                score -= 15
                recommendations.append(
                    {
                        "text": "CPU usage very high - check resource-heavy processes",
                        "severity": "high",
                        "category": "CPU",
                    }
                )
            elif cpu > 50:
                score -= 5
                recommendations.append(
                    {
                        "text": "CPU usage elevated - review background processes",
                        "severity": "low",
                        "category": "CPU",
                    }
                )

            # Disk usage
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    if usage.percent > 90:
                        score -= 15
                        recommendations.append(
                            {
                                "text": f"Disk {part.device} nearly full ({usage.percent}%) - free space",
                                "severity": "high",
                                "category": "Disk",
                            }
                        )
                    elif usage.percent > 75:
                        score -= 5
                        recommendations.append(
                            {
                                "text": f"Disk {part.device} at {usage.percent}% - consider cleanup",
                                "severity": "medium",
                                "category": "Disk",
                            }
                        )
                except (PermissionError, OSError):
                    pass

        # Temp files
        temp_info = opt_results.get("Temp Files Analysis", {})
        total_temp = temp_info.get("total_size", 0) if isinstance(temp_info, dict) else 0
        if total_temp > 500_000_000:
            score -= 10
            recommendations.append(
                {
                    "text": f"Large temp files cache ({total_temp / (1024**3):.1f} GB) - run cleanup",
                    "severity": "medium",
                    "category": "Cleanup",
                }
            )
        elif total_temp > 100_000_000:
            score -= 3
            recommendations.append(
                {
                    "text": "Temp files present - periodic cleanup recommended",
                    "severity": "low",
                    "category": "Cleanup",
                }
            )

        # Startup programs
        startup = opt_results.get("Startup Impact", [])
        if isinstance(startup, list) and len(startup) > 10:
            score -= 8
            recommendations.append(
                {
                    "text": f"{len(startup)} startup programs - disable unnecessary ones",
                    "severity": "medium",
                    "category": "Startup",
                }
            )
        elif isinstance(startup, list) and len(startup) > 5:
            score -= 3
            recommendations.append(
                {
                    "text": f"{len(startup)} startup programs - review for optimization",
                    "severity": "low",
                    "category": "Startup",
                }
            )

        # Optimizable services
        services = opt_results.get("Services", [])
        if isinstance(services, list):
            running_optional = [
                s
                for s in services
                if isinstance(s, dict) and s.get("can_optimize") and s.get("status") == "Running"
            ]
            if len(running_optional) > 5:
                score -= 8
                recommendations.append(
                    {
                        "text": f"{len(running_optional)} optional services running - disable for performance",
                        "severity": "medium",
                        "category": "Services",
                    }
                )
            elif running_optional:
                score -= 3
                recommendations.append(
                    {
                        "text": f"{len(running_optional)} optional services could be disabled",
                        "severity": "low",
                        "category": "Services",
                    }
                )

        # Visual effects
        ve = opt_results.get("Visual Effects", {})
        if isinstance(ve, dict) and ve.get("current_mode") == "Best appearance":
            score -= 5
            recommendations.append(
                {
                    "text": "Visual effects set to 'Best appearance' - switch to Performance",
                    "severity": "low",
                    "category": "Graphics",
                }
            )

        # Power plan
        power = opt_results.get("Power Plans", [])
        if isinstance(power, list):
            active = [p for p in power if isinstance(p, dict) and p.get("active")]
            if active:
                name = active[0].get("name", "").lower()
                if "power saver" in name or "balanced" in name:
                    score -= 5
                    recommendations.append(
                        {
                            "text": "Power plan not set to High Performance",
                            "severity": "low",
                            "category": "Power",
                        }
                    )

        if not recommendations:
            recommendations.append(
                {"text": "System is well optimized!", "severity": "ok", "category": "General"}
            )

        return max(0, min(100, score)), recommendations
