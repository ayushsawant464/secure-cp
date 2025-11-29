# Phase 2 Bug Fixes - IPv6 and iptables Rollback

## Issues Fixed

### 1. IPv6 Address Handling in Domain Filter
**Problem:** Domain filter was trying to add IPv6 addresses using regular `iptables` command, which only supports IPv4.

**Error:**
```
iptables v1.8.10 (nf_tables): host/network `2606:4700:3035::6815:afc' not found
```

**Solution:**
- Separated IPv4 and IPv6 address resolution into `allowed_ips_v4` and `allowed_ips_v6` sets
- Use `iptables` for IPv4 addresses only
- Use `ip6tables` for IPv6 addresses
- Create separate filter chains: `EXAM_FILTER` (IPv4) and `EXAM_FILTER_V6` (IPv6)

### 2. iptables Rollback in Production Mode
**Problem:** VPN manager and domain filter modify iptables rules without backing them up first. In production mode, this would permanently change the user's iptables configuration.

**Solution:**
- Added `backup_iptables()` method to save current rules before modifying
- Added `restore_iptables()` method to restore original rules on cleanup
- In testing mode: just delete chains (namespace is destroyed anyway)  
- In production mode: restore complete original iptables state

## Files Modified

- [domain_filter.py](file:///home/savvy19/Desktop/product/secure-exam-system/network/domain_filter.py)
  - Separated IPv4/IPv6 handling
  - Added backup/restore methods
  - IPv6 rules only added if IPv6 addresses exist

## Testing

Run the Phase 2 tests to verify fixes:
```bash
cd /home/savvy19/Desktop/product/secure-exam-system
sudo python3 tests/test_phase2.py
```

Expected: Domain filter test should now pass without IPv6 errors.
