commands=(
nmap masscan rustscan netdiscover arp-scan fping whois dig host theharvester sublist3r amass dnsenum dnsrecon enum4linux smbclient smbmap crackmapexec rpcclient ldapsearch nikto gobuster feroxbuster dirb dirsearch wfuzz ffuf sqlmap burpsuite zap msfconsole msfvenom hashcat john hydra medusa patator ncat nc socat tcpdump tshark wireshark bettercap mitmproxy responder ettercap airmon-ng airodump-ng aireplay-ng aircrack-ng reaver wash wifite crowbar cewl whatweb wafw00f sslscan sslyze openssl gpg wpscan onesixtyone imap-user-enum smtp-user-enum
)

# Met à jour le cache tldr (optionnel)
tldr --update >/dev/null 2>&1

for c in "${commands[@]}"; do
  if tldr "$c" >/dev/null 2>&1; then
    echo "$c: OK"
  else
    echo "$c: MISSING"
  fi
done
