/* ============================================
   ROYAL BROTHERS FITNESS GYM - PROFILE PAGE
   Loads profile info + membership status, editable profile fields,
   expiry warning, and logout.

   Profile photo upload has been removed. Every user's avatar is the
   fixed official gym image (app/static/royalbrothersgym.jpg), set
   directly in profile.html -- there is no per-user image logic here.
   ============================================ */

document.addEventListener("DOMContentLoaded", () => {
  loadProfile();
  loadMembershipCard();
  initEditProfile();
  initLogout();
});

/* ---------- TOAST HELPER ---------- */
function showToast(message, isError) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", !!isError);
  toast.classList.add("show");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => toast.classList.remove("show"), 4000);
}

/* ---------- SAFE FETCH HELPER ----------
   Distinguishes three outcomes so error messages are always accurate:
     1. Network/server unreachable -> fetch() itself throws (TypeError)
     2. Server reachable but sent a non-JSON body (e.g. a 404/405 HTML
        error page from a missing route) -> res.json() throws
     3. Server reachable and responded with JSON, success or failure
   Returns { ok, status, data, networkError, badResponse }.
------------------------------------------- */
async function safeFetch(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch (err) {
    // fetch() only throws for actual network failures (server down,
    // no internet, CORS block, DNS failure, etc.) -- this is the ONLY
    // case that should ever show "Could not reach the server."
    return {
      ok: false,
      networkError: true,
      badResponse: false,
      status: 0,
      data: null,
    };
  }

  let data = null;
  try {
    data = await res.json();
  } catch (err) {
    // Server responded, but not with JSON (e.g. a missing-route 404/405
    // HTML page). This is a server-side/routing bug, not a network issue.
    return {
      ok: false,
      networkError: false,
      badResponse: true,
      status: res.status,
      data: null,
    };
  }

  return {
    ok: res.ok,
    networkError: false,
    badResponse: false,
    status: res.status,
    data,
  };
}

/* ---------- LOAD PROFILE ----------
   Uses AuthCache (see auth-cache.js) so this shares its /api/auth/me
   call with script.js's navbar check instead of firing a second,
   separate request on the same page load -- and can paint instantly
   from cache while that shared call is still in flight. */
async function loadProfile() {
  const loadingEl = document.getElementById("profileLoading");
  const loggedOutEl = document.getElementById("profileLoggedOut");
  const contentEl = document.getElementById("profileContent");

  // ---------- Instant paint from cache (no network wait) ----------
  const cached = window.AuthCache ? window.AuthCache.getCachedUser() : null;
  if (cached && cached.ok && cached.data && cached.data.success) {
    applyProfileToUI(cached.data.user);
    loadingEl.style.display = "none";
    contentEl.style.display = "block";
  }

  const fetchUser = window.AuthCache
    ? window.AuthCache.fetchUser
    : () =>
        fetch("/api/auth/me", { credentials: "include" })
          .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
          .catch(() => ({ ok: false, data: null, networkError: true }));

  const result = await fetchUser();

  if (result.networkError && !cached) {
    loadingEl.textContent =
      "Could not reach the server. Please try again later.";
    return;
  }

  if (!result.ok || !result.data || !result.data.success) {
    // Not logged in (or the cached state above was stale) -- show the
    // logged-out state, same as before.
    loadingEl.style.display = "none";
    contentEl.style.display = "none";
    loggedOutEl.style.display = "block";
    return;
  }

  const user = result.data.user;
  applyProfileToUI(user);

  loadingEl.style.display = "none";
  contentEl.style.display = "block";
}

/* ---------- APPLY PROFILE DATA TO THE UI ----------
   Single source of truth for painting profile fields, called after
   the initial load AND after a successful save, so the page never
   needs a refresh to reflect the latest data.
------------------------------------------------------ */
function applyProfileToUI(user) {
  document.getElementById("profileName").textContent = user.full_name;
  document.getElementById("profileEmail").textContent = user.email;
  document.getElementById("profileGender").textContent = user.gender;
  document.getElementById("editFullName").value = user.full_name;
  document.getElementById("editGender").value = user.gender;
}

/* ---------- EDIT PROFILE (name + gender) ---------- */
function initEditProfile() {
  const viewMode = document.getElementById("profileViewMode");
  const editForm = document.getElementById("editProfileForm");
  const editBtn = document.getElementById("editProfileBtn");
  const cancelBtn = document.getElementById("cancelEditBtn");
  const errorBox = document.getElementById("editProfileError");

  if (!editForm) return;

  function showError(text) {
    errorBox.textContent = text;
    errorBox.classList.toggle("show", !!text);
  }

  editBtn.addEventListener("click", () => {
    viewMode.style.display = "none";
    editForm.style.display = "block";
    showError("");
  });

  cancelBtn.addEventListener("click", () => {
    editForm.style.display = "none";
    viewMode.style.display = "block";
    showError("");
  });

  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");

    const fullName = document.getElementById("editFullName").value.trim();
    const gender = document.getElementById("editGender").value;

    // ---------- Client-side validation ----------
    if (!fullName) {
      showError("Name cannot be empty.");
      return;
    }

    if (fullName.length > 100) {
      showError("Name must be 100 characters or fewer.");
      return;
    }

    if (!["male", "female", "other"].includes(gender)) {
      showError("Please select a valid gender.");
      return;
    }

    const saveBtn = document.getElementById("saveProfileBtn");
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    const result = await safeFetch("/api/auth/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ fullName, gender }),
    });

    saveBtn.disabled = false;
    saveBtn.textContent = originalText;

    if (result.networkError) {
      showError("Could not reach the server. Please try again later.");
      return;
    }

    if (result.badResponse) {
      // Server responded but not with JSON -- a real server-side
      // problem, not a network issue. Report it accurately instead of
      // calling it a network error.
      showError(
        `Server error (status ${result.status}). Please try again, or contact support if this continues.`,
      );
      return;
    }

    if (result.ok && result.data && result.data.success) {
      // Update the UI immediately from the server's confirmed data --
      // no page refresh needed.
      applyProfileToUI(result.data.user);
      if (window.AuthCache) window.AuthCache.setCachedUser(result.data.user);
      editForm.style.display = "none";
      viewMode.style.display = "block";
      showToast(result.data.message || "Profile updated successfully.", false);
      return;
    }

    // Server responded with valid JSON but reported a failure
    // (validation error, not logged in, etc.) -- show its message.
    showError(
      (result.data && result.data.message) || "Could not update profile.",
    );

    if (result.status === 401) {
      // Session expired/not logged in -- send them to log back in.
      showToast("Your session has expired. Please log in again.", true);
      setTimeout(() => {
        window.location.href = "login.html";
      }, 1500);
    }
  });
}

/* ---------- MEMBERSHIP CARD + EXPIRY WARNING ---------- */
async function loadMembershipCard() {
  const wrap = document.getElementById("membershipCardWrap");
  const warningBox = document.getElementById("expiryWarning");
  const warningText = document.getElementById("expiryWarningText");

  const result = await safeFetch("/api/membership/my-request", {
    credentials: "include",
  });

  if (result.networkError) {
    wrap.innerHTML =
      '<p class="profile-status">Could not reach the server.</p>';
    return;
  }

  if (
    result.badResponse ||
    !result.ok ||
    !result.data ||
    !result.data.success
  ) {
    wrap.innerHTML =
      '<p class="profile-status">Could not load membership info.</p>';
    return;
  }

  const req = result.data.request;

  if (!req) {
    wrap.innerHTML = `
      <div class="membership-card-empty">
        You don't have a membership yet.<br />
        <a href="membership.html">View plans and get started</a>
      </div>`;
    return;
  }

  wrap.innerHTML = `
    <div class="membership-card">
      <div class="membership-card-header">
        <h3>Royal Brothers Fitness Gym</h3>
        <span class="status-badge ${req.status}">${req.status}</span>
      </div>
      <div class="membership-card-row">
        <span>Plan</span>
        <span>${req.plan_name}</span>
      </div>
      <div class="membership-card-row">
        <span>Request Date</span>
        <span>${new Date(req.request_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
      </div>
      ${
        req.start_date
          ? `
      <div class="membership-card-row">
        <span>Start Date</span>
        <span>${new Date(req.start_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
      </div>`
          : ""
      }
      ${
        req.end_date
          ? `
      <div class="membership-card-row">
        <span>Expiry Date</span>
        <span>${new Date(req.end_date).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</span>
      </div>`
          : ""
      }
    </div>`;

  // ---------- Expiry warning (Bug 7) ----------
  if (req.status === "active" && req.end_date) {
    const today = new Date();
    const expiry = new Date(req.end_date);
    const daysLeft = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));

    if (daysLeft <= 7 && daysLeft >= 0) {
      warningText.textContent = `Your membership expires in ${daysLeft} day${daysLeft === 1 ? "" : "s"}.`;
      warningBox.style.display = "flex";
    } else if (daysLeft < 0) {
      warningText.textContent =
        "Your membership has expired. Please renew at Royal Brothers Fitness Gym.";
      warningBox.style.display = "flex";
    }
  }
}

/* ---------- LOGOUT ----------
   Handles both the navbar logout button (#logoutBtn, unchanged
   behavior) and the new profile-page bottom logout button
   (#logoutBtnProfile), which asks for confirmation first. Both share
   the same performLogout() call to the existing logout API so there
   is only one place that talks to the server / clears the cache. */
function initLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  const logoutBtnProfile = document.getElementById("logoutBtnProfile");

  async function performLogout() {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      if (window.AuthCache) window.AuthCache.clearCache();
      window.location.href = "login.html";
    }
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", performLogout);
  }

  if (logoutBtnProfile) {
    logoutBtnProfile.addEventListener("click", () => {
      const confirmed = window.confirm("Are you sure you want to logout?");
      if (confirmed) {
        performLogout();
      }
    });
  }
}
