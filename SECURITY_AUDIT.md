# Security Audit Report: Justyol Dashboard
**Date:** February 11, 2026  
**Status:** ⚠️ Multiple Issues Found

---

## Executive Summary

The Justyol Dashboard application has **several security vulnerabilities and general code quality issues** that should be addressed before production deployment. While no critical SQL injection flaws were identified (due to Frappe's parameterized queries), there are significant concerns around **authorization, data exposure, cache security, and frontend vulnerabilities**.

---

## 🔴 CRITICAL ISSUES

### 1. **Missing Authorization Checks on All API Endpoints**
**Severity:** CRITICAL  
**Location:** All files in `justyol_dashboard/api/*.py`  
**Issue:** All 14 API endpoints are decorated with `@frappe.whitelist()` without any role-based access control.

**Example (alerts.py):**
```python
@frappe.whitelist()  # ❌ No authorization check
def get_alerts_dashboard(company="Justyol Morocco"):
    """Any logged-in user can call this"""
```

**Impact:**
- Any authenticated user can access sensitive financial, customer, and inventory data for ANY company
- No checks for whether the user belongs to the requested company
- Users can retrieve data they shouldn't have access to

**Recommendation:**
```python
import frappe
from frappe.exceptions import PermissionError

@frappe.whitelist()
def get_alerts_dashboard(company="Justyol Morocco"):
    # Check if user has access to this company
    if not frappe.has_permission("Company", "read", company):
        raise PermissionError(f"Not allowed to access company: {company}")
    
    # Or check user roles:
    allowed_roles = ["Dashboard Manager", "Executive"]
    if not any(role in frappe.get_roles() for role in allowed_roles):
        raise PermissionError("Only Dashboard Managers can view alerts")
```

---

### 2. **Hardcoded Company Names as Defaults**
**Severity:** CRITICAL  
**Location:** All API files (alerts.py, sales.py, finance.py, etc.)  
**Issue:** All functions have hardcoded default company `company="Justyol Morocco"`

**Example:**
```python
def get_alerts_dashboard(company="Justyol Morocco"):
def get_sales_dashboard(company="Justyol Morocco", ...):
def get_finance_dashboard(company="Justyol Morocco", ...):
```

**Impact:**
- If an unauthorized user calls these endpoints without specifying a company parameter, they get Justyol Morocco data
- No validation that the requested company exists or that the user has access

**Recommendation:**
```python
@frappe.whitelist()
def get_alerts_dashboard(company=None):
    # Use current user's company, don't provide a default
    if not company:
        company = frappe.get_value("User", frappe.session.user, "company")
    
    if not company:
        raise ValueError("User has no default company assigned")
    
    # Validate access
    if not frappe.has_permission("Company", "read", company):
        raise PermissionError(f"Access denied to {company}")
    
    cache_key = f"dashboard:alerts:{company}"
    # ... rest of code
```

---

### 3. **Cache Key Collision / Data Leakage**
**Severity:** HIGH  
**Location:** `justyol_dashboard/services/cache_service.py`  
**Issue:** Cache is shared across all companies and users, keyed only by company name

**Current Code:**
```python
def get_cached(key, compute_fn, ttl=CACHE_TTL, **kwargs):
    cached = frappe.cache().get_value(key)  # ❌ No user isolation
    if cached:
        return cached
    result = compute_fn(**kwargs)
    frappe.cache().set_value(key, result, expires_in_sec=ttl)
    return result
```

**Example Vulnerable Call:**
```python
cache_key = f"dashboard:alerts:{company}"  # ❌ Missing user context
```

**Impact:**
- User A retrieves data for a company, which gets cached
- User B (even if unauthorized) might receive cached data from User A's request
- Cache invalidation doesn't account for user-specific permissions

**Recommendation:**
```python
def get_cached(key, compute_fn, ttl=CACHE_TTL, user=None, **kwargs):
    # Always include user in cache key
    user = user or frappe.session.user
    isolated_key = f"{key}:user:{user}"
    
    cached = frappe.cache().get_value(isolated_key)
    if cached:
        return cached
    
    result = compute_fn(**kwargs)
    frappe.cache().set_value(isolated_key, result, expires_in_sec=ttl)
    return result
```

---

### 4. **Unvalidated Company Parameter (Multiple Files)**
**Severity:** HIGH  
**Location:** All API files  
**Issue:** The `company` parameter is never validated to exist or be accessible by the user

**Example (customers.py):**
```python
@frappe.whitelist()
def get_customer_dashboard(company="Justyol Morocco", period="month"):
    # ❌ No validation that company exists or user has access
    cache_key = f"dashboard:customers:{company}:{dates['from']}:{dates['to']}"
    
    # Directly queries using unvalidated company value
    customer_kpis = frappe.db.sql("""
        SELECT ... FROM `tabSales Order`
        WHERE company = %s  # Parameterized, but not validated
    """, (company, from_date, to_date), as_dict=True)[0]
```

**Recommendation:**
```python
def validate_company(company):
    """Validate company exists and user has access"""
    if not frappe.db.exists("Company", company):
        raise ValueError(f"Company does not exist: {company}")
    
    if not frappe.has_permission("Company", "read", company):
        raise PermissionError(f"Access denied to {company}")
    
    return company

@frappe.whitelist()
def get_customer_dashboard(company="Justyol Morocco", period="month"):
    company = validate_company(company)
    # ... rest of code
```

---

## 🟠 HIGH PRIORITY ISSUES

### 5. **Sensitive Data Exposed in Real-time Updates**
**Severity:** HIGH  
**Location:** `justyol_dashboard/api/realtime.py`  
**Issue:** Financial data sent to ALL connected users without filtering

```python
def on_sales_order_change(doc, method):
    push_dashboard_update(
        event_type="sales_order_update",
        data={
            "order_name": doc.name,
            "customer": doc.customer,
            "grand_total": float(doc.grand_total or 0),  # ❌ Broadcast to all
            "sales_status": doc.custom_sales_status,
            # ...
        },
        company=doc.company,  # ⚠️ Only filters by company, not by user
    )
```

**Impact:**
- All users viewing the same company see order details, including grand_total
- No row-level security on real-time updates

**Recommendation:**
```python
def on_sales_order_change(doc, method):
    # Only push to users with permission
    allowed_users = frappe.db.get_list("User", 
        filters={"company": doc.company}, 
        pluck="name"
    )
    
    for user in allowed_users:
        if frappe.has_permission("Sales Order", "read", doc.name, user=user):
            push_to_user(user, "sales_order_update", {...})
```

---

### 6. **Missing Input Validation on Period Parameter**
**Severity:** MEDIUM-HIGH  
**Location:** All API files (alerts.py, sales.py, finance.py, etc.)  
**Issue:** Period parameter is passed directly without validation

```python
@frappe.whitelist()
def get_sales_dashboard(company="Justyol Morocco", 
                       from_date=None, to_date=None, 
                       period="today"):  # ❌ No validation
    if from_date and to_date:
        dates = {"from": from_date, "to": to_date}
    else:
        dates = get_period_dates(period)  # What if period has invalid value?
```

**Recommendation:**
```python
VALID_PERIODS = ["today", "yesterday", "week", "month", "last_month", "quarter", "year"]

@frappe.whitelist()
def get_sales_dashboard(company="Justyol Morocco", 
                       from_date=None, to_date=None, 
                       period="today"):
    # Validate period
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period. Must be one of: {VALID_PERIODS}")
    
    # Validate custom dates if provided
    if from_date and to_date:
        try:
            f = frappe.utils.getdate(from_date)
            t = frappe.utils.getdate(to_date)
            if f > t:
                raise ValueError("from_date cannot be after to_date")
        except:
            raise ValueError("Invalid date format")
        dates = {"from": from_date, "to": to_date}
    else:
        dates = get_period_dates(period)
```

---

### 7. **Frontend localStorage Security Issue**
**Severity:** MEDIUM  
**Location:** `justyol_dashboard/public/js/App.vue`  
**Issue:** Storing company preference in localStorage allows XSS attacks

```javascript
const selectedCompany = ref(
    localStorage.getItem("justyol_company") || "Justyol Morocco"  // ❌ Vulnerable
);

function setCompany(company) {
    selectedCompany.value = company;
    localStorage.setItem("justyol_company", company);  // ❌ No validation
}
```

**Impact:**
- Reflected XSS could inject malicious values into localStorage
- Company selection bypasses server-side validation

**Recommendation:**
```javascript
const VALID_COMPANIES = ["Justyol Morocco", "Justyol China", "Justyol Holding", "Maslak LTD"];

function setCompany(company) {
    // Validate company
    if (!VALID_COMPANIES.includes(company)) {
        console.error("Invalid company:", company);
        return;
    }
    selectedCompany.value = company;
    localStorage.setItem("justyol_company", company);
}

onMounted(() => {
    const stored = localStorage.getItem("justyol_company");
    if (stored && VALID_COMPANIES.includes(stored)) {
        selectedCompany.value = stored;
    }
});
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 8. **Missing CORS Headers and CSP Configuration**
**Severity:** MEDIUM  
**Location:** Global (vite.config.js, app configuration)  
**Issue:** No mention of CORS, CSP, or security headers configuration

**Recommendation:**
- Configure Content Security Policy (CSP) headers
- Set proper CORS policies if needed
- Add security headers (X-Frame-Options, X-Content-Type-Options, etc.)

---

### 9. **No Rate Limiting on API Endpoints**
**Severity:** MEDIUM  
**Location:** All API endpoints  
**Issue:** 14 API endpoints with no rate limiting - vulnerable to DoS attacks

**Recommendation:**
```python
from frappe.utils.rate_limit import rate_limit

@frappe.whitelist()
@rate_limit(limit_by="User", key=lambda *args, **kwargs: frappe.session.user)
def get_alerts_dashboard(company="Justyol Morocco"):
    # Rate limited per user
    pass
```

---

### 10. **Hardcoded TTL Values Without Context**
**Severity:** LOW-MEDIUM  
**Location:** `justyol_dashboard/services/cache_service.py`  
**Issue:** Different files use different TTLs inconsistently

```python
# cache_service.py
CACHE_TTL = 120  # 2 minutes default

# alerts.py
return get_cached(cache_key, compute, ttl=60)  # 1 minute

# inventory.py
return get_cached(cache_key, compute, ttl=180)  # 3 minutes

# finance.py (default, no ttl specified) -> uses 120
return get_cached(cache_key, compute)  # 2 minutes
```

**Impact:**
- Inconsistent data freshness across dashboards
- Financial data might be stale or outdated
- No strategy for invalidation on data changes

**Recommendation:**
```python
# Define TTL by dashboard type and data sensitivity
CACHE_TTL_SETTINGS = {
    "alerts": 60,           # 1 min - critical alerts
    "finance": 300,         # 5 min - less time-sensitive
    "realtime": 30,         # 30 sec - very current
    "customer": 600,        # 10 min - less critical
}

def get_cached(key, compute_fn, dashboard_type="default", **kwargs):
    ttl = CACHE_TTL_SETTINGS.get(dashboard_type, 120)
    # ... rest of code
```

---

### 11. **SQL Queries Not Optimized / No Explain Plans**
**Severity:** LOW-MEDIUM  
**Location:** All API files (especially customers.py, finance.py)  
**Issue:** Complex SQL queries without visible optimization

**Example (customers.py - expensive subquery):**
```python
# Inefficient: checks prior orders one-by-one for each customer
for c in repeat_data:
    prior = frappe.db.count("Sales Order", {
        "company": company,
        "customer": c.customer,
        "creation": ["<", from_date],  # N+1 queries
    })
```

**Recommendation:**
```python
# Use a single query instead
repeat_data = frappe.db.sql("""
    SELECT
        c.customer,
        COUNT(c.name) as order_count,
        SUM(c.grand_total) as total_spend,
        MIN(c.creation) as first_order,
        (SELECT COUNT(*) FROM `tabSales Order` s2 
         WHERE s2.customer = c.customer 
         AND s2.creation < %s) as prior_orders
    FROM `tabSales Order` c
    WHERE c.company = %s
        AND c.creation >= %s
        AND c.creation <= %s
    GROUP BY c.customer
""", (from_date, company, from_date, to_date), as_dict=True)
```

---

### 12. **No Error Handling for Cache Operations**
**Severity:** LOW-MEDIUM  
**Location:** `justyol_dashboard/services/cache_service.py`  
**Issue:** Cache failures could crash the dashboard

```python
def get_cached(key, compute_fn, ttl=CACHE_TTL, **kwargs):
    cached = frappe.cache().get_value(key)  # ❌ No try-catch
    if cached:
        return cached
    
    result = compute_fn(**kwargs)
    frappe.cache().set_value(key, result, expires_in_sec=ttl)  # ❌ Could fail
    return result
```

**Recommendation:**
```python
def get_cached(key, compute_fn, ttl=CACHE_TTL, **kwargs):
    try:
        cached = frappe.cache().get_value(key)
        if cached:
            return cached
    except Exception as e:
        frappe.log_error(f"Cache retrieval failed: {str(e)}")
        # Fall through to compute
    
    result = compute_fn(**kwargs)
    
    try:
        frappe.cache().set_value(key, result, expires_in_sec=ttl)
    except Exception as e:
        frappe.log_error(f"Cache write failed: {str(e)}")
        # Return result anyway, just not cached
    
    return result
```

---

### 13. **Missing Input Validation in TopBar Component**
**Severity:** LOW  
**Location:** `justyol_dashboard/public/js/components/TopBar.vue`  
**Issue:** Company selector doesn't validate selection

```vue
<select :value="company" @change="$emit('company-change', $event.target.value)">
    <!-- ❌ No validation of selected value -->
</select>
```

**Recommendation:**
```vue
<select :value="company" @change="changeCompany">

<script>
function changeCompany(event) {
    const selected = event.target.value;
    if (VALID_COMPANIES.includes(selected)) {
        $emit('company-change', selected);
    } else {
        console.error("Invalid company selected");
    }
}
</script>
```

---

### 14. **No Audit Logging for Sensitive Operations**
**Severity:** LOW-MEDIUM  
**Location:** All API endpoints  
**Issue:** No logging of who accessed what data and when

**Recommendation:**
```python
import frappe

def audit_log(action, company, details=None):
    """Log dashboard access for compliance"""
    frappe.db.insert({
        "doctype": "Dashboard Access Log",
        "user": frappe.session.user,
        "action": action,
        "company": company,
        "details": str(details),
        "timestamp": frappe.utils.now(),
    })

@frappe.whitelist()
def get_alerts_dashboard(company="Justyol Morocco"):
    audit_log("view_alerts", company)
    # ... rest of code
```

---

## 📋 GENERAL CODE QUALITY ISSUES

### 15. **Inconsistent Error Handling**
- No validation of SQL query results (e.g., `[0]` access without checking list length)
- No try-catch blocks in API methods
- Frontend doesn't handle API errors gracefully

### 16. **Missing Type Hints**
- Python files lack type annotations
- Hard to understand function contracts

### 17. **Hardcoded Magic Numbers**
- `LIMIT 20`, `LIMIT 10`, `LIMIT 5` scattered throughout
- No constants defined for these values

### 18. **No Tests or Test Coverage**
- No unit tests for API endpoints
- No integration tests for cache operations
- Frontend has no component tests

### 19. **Unused CSS Classes**
- Many commented-out sections in CSS
- No minification/optimization evident

### 20. **Missing Documentation**
- No API documentation (OpenAPI/Swagger)
- No deployment guide
- No security.md guidelines

---

## 🔧 Recommended Fixes (Priority Order)

| Priority | Issue | Fix Time | Effort |
|----------|-------|----------|--------|
| **P0** | Missing authorization checks | 2-3 hours | High |
| **P0** | Hardcoded company defaults | 1-2 hours | Medium |
| **P0** | Cache key collision | 1-2 hours | Medium |
| **P1** | Input validation on parameters | 2-3 hours | Medium |
| **P1** | Real-time data filtering | 1-2 hours | Medium |
| **P2** | Rate limiting | 1 hour | Low |
| **P2** | Error handling & logging | 2-3 hours | Medium |
| **P3** | Code quality improvements | 3-4 hours | Low |

---

## ✅ Compliance Checklist

- [ ] All API endpoints have authorization checks
- [ ] No hardcoded company defaults
- [ ] Cache keys include user context
- [ ] Input validation on all parameters
- [ ] Real-time updates respect permissions
- [ ] Rate limiting configured
- [ ] Audit logging implemented
- [ ] Error handling in place
- [ ] Security headers configured
- [ ] Code reviewed by security team

---

## Next Steps

1. **Immediate:** Implement authorization checks on all endpoints (blocking issue)
2. **This week:** Fix cache isolation and input validation
3. **This sprint:** Add rate limiting, audit logging, and error handling
4. **Ongoing:** Code quality improvements and test coverage

Would you like me to implement any of these fixes?
