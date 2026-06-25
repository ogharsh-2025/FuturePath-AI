/**
 * ==========================================================================
 * FUTUREPATH.AI - CLIENT SIDE APPLICATION CONTROLLER
 * ==========================================================================
 */

// Determine API Base URL automatically
const API_BASE = window.location.hostname.includes("render.com") || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? ""
    : "https://futurepath-backend-rn47.onrender.com";

// Application state persistence
const state = {
    token: localStorage.getItem("token") || null,
    role: localStorage.getItem("role") || null,
    user: JSON.parse(localStorage.getItem("user")) || null,
    activeResume: null,
    currentJobId: null,
    charts: {} // Store active ChartJS instances
};

// ==========================================================================
// Toast Alerts Helper
// ==========================================================================
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconClass = "fa-info-circle";
    if (type === "success") iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-triangle-exclamation";

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// ==========================================================================
// HTTP Client Request Helper
// ==========================================================================
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    options.headers = options.headers || {};
    if (state.token && !options.headers["Authorization"]) {
        options.headers["Authorization"] = `Bearer ${state.token}`;
    }
    
    if (!(options.body instanceof FormData) && options.body && typeof options.body === "object") {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            handleLogout();
            showToast("Session expired or unauthorized.", "error");
            return null;
        }

        if (response.status === 204) {
            return true;
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "Request failed");
            }
            return data;
        } else {
            if (!response.ok) {
                const txt = await response.text();
                throw new Error(txt || `Request failed: ${response.status}`);
            }
            return await response.blob();
        }
    } catch (error) {
        console.error("API error:", error.message);
        showToast(error.message, "error");
        throw error;
    }
}

// ==========================================================================
// SPA ROUTER DEFINITION
// ==========================================================================
const views = {
    login: document.getElementById("view-login"),
    register: document.getElementById("view-register"),
    dashboard: document.getElementById("view-dashboard"),
    jobs: document.getElementById("view-jobs"),
    jobDetails: document.getElementById("view-job-details"),
    "resume-analyzer": document.getElementById("view-resume-analyzer"),
    "mock-interview": document.getElementById("view-mock-interview"),
    "github-analyzer": document.getElementById("view-github-analyzer"),
    roadmap: document.getElementById("view-roadmap"),
    "salary-trends": document.getElementById("view-salary-trends"),
    settings: document.getElementById("view-settings"),
    upload: document.getElementById("view-upload")
};

function router() {
    let hash = window.location.hash || "#dashboard";
    
    let viewKey = hash.substring(1);
    let extraParam = null;
    
    if (viewKey.includes("/")) {
        const parts = viewKey.split("/");
        viewKey = parts[0];
        extraParam = parts[1];
    }

    console.log("Routing to view:", viewKey, "Param:", extraParam);

    // Enforce Auth Guard
    if (viewKey === "login" || viewKey === "register") {
        if (state.token) {
            window.location.hash = "#dashboard";
            return;
        }
        document.getElementById("sidebar").style.display = "none";
        document.getElementById("app-header").style.display = "none";
        document.getElementById("app-main").style.marginLeft = "0";
    } else {
        if (!state.token) {
            window.location.hash = "#login";
            return;
        }
        document.getElementById("sidebar").style.display = "";
        document.getElementById("app-header").style.display = "";
        document.getElementById("app-main").style.marginLeft = "";
    }

    // Toggle View active classes
    Object.keys(views).forEach(key => {
        if (views[key]) {
            views[key].classList.remove("active");
        }
    });

    if (views[viewKey]) {
        views[viewKey].classList.add("active");
        document.getElementById("breadcrumb-active").innerText = viewKey.replace("-", " ").toUpperCase();
    } else {
        if (state.token) {
            views.dashboard.classList.add("active");
            document.getElementById("breadcrumb-active").innerText = "DASHBOARD";
            window.location.hash = "#dashboard";
        } else {
            views.login.classList.add("active");
            window.location.hash = "#login";
        }
    }

    // Toggle menu items active style
    document.querySelectorAll(".menu-item").forEach(item => {
        item.classList.remove("active");
        if (item.getAttribute("data-view") === viewKey) {
            item.classList.add("active");
        }
    });

    // Toggle mobile navigation items active style
    document.querySelectorAll(".mobile-nav-item").forEach(item => {
        item.classList.remove("active");
        if (item.getAttribute("data-view") === viewKey) {
            item.classList.add("active");
        }
    });

    document.getElementById("sidebar").classList.remove("open");

    // Load Data for specific views
    if (viewKey === "dashboard") {
        loadDashboard();
    } else if (viewKey === "jobs") {
        loadJobsList();
    } else if (viewKey === "jobDetails" && extraParam) {
        state.currentJobId = extraParam;
        loadJobDetails(extraParam);
    } else if (viewKey === "mock-interview") {
        loadMockInterviewHistory();
    } else if (viewKey === "salary-trends") {
        loadSalaryAndTrends();
    } else if (viewKey === "settings") {
        loadSettings();
    } else if (viewKey === "roadmap") {
        loadRoadmap(extraParam);
    }
}

// Helper to safely clean up and initialize charts
function drawChart(canvasId, type, config) {
    if (state.charts[canvasId]) {
        state.charts[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId);
    if (ctx) {
        state.charts[canvasId] = new Chart(ctx, {
            type: type,
            ...config
        });
    }
}

// ==========================================================================
// VIEW LOADERS & API CONNECTORS
// ==========================================================================

// 1. Dashboard View Loader
async function loadDashboard() {
    const resumeEmpty = document.getElementById("resume-empty-state");
    const resumeDetails = document.getElementById("resume-details-container");
    const skillsCloud = document.getElementById("resume-skills-cloud");
    const matchesList = document.getElementById("dash-matches-list");
    const matchesCount = document.getElementById("dash-matches-count");

    updateUserWidgetUI();

    matchesList.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Matching jobs...</p></div>`;

    try {
        const notifs = await apiRequest("/api/notifications");
        const unreadCount = notifs.filter(n => !n.is_read).length;
        const badge = document.getElementById("menu-notif-count");
        const indicator = document.getElementById("header-notif-indicator");
        
        if (unreadCount > 0) {
            badge.innerText = unreadCount;
            badge.classList.remove("hidden");
            indicator.classList.remove("hidden");
        } else {
            badge.classList.add("hidden");
            indicator.classList.add("hidden");
        }

        const resume = await apiRequest("/api/resumes/my-resume").catch(() => null);
        state.activeResume = resume;

        if (resume) {
            resumeEmpty.classList.add("hidden");
            resumeDetails.classList.remove("hidden");
            document.getElementById("resume-filename").innerText = resume.resume_file.split(/[\\/]/).pop().replace(/^user_\d+_/, "");
            skillsCloud.innerHTML = resume.skills.map(s => `<span class="tag">${s.skill_name}</span>`).join("");

            document.getElementById("kpi-ats-score").innerText = "84%";
            document.getElementById("kpi-github-score").innerText = "78%";

            const attempts = await apiRequest("/api/interview-prep/history").catch(() => []);
            if (attempts.length > 0) {
                const avgScore = Math.round(attempts.reduce((acc, a) => acc + a.score, 0) / attempts.length);
                document.getElementById("kpi-interview-score").innerText = `${avgScore}%`;
            } else {
                document.getElementById("kpi-interview-score").innerText = "N/A";
            }

            const recs = await apiRequest("/api/recommendations/");
            if (recs && recs.length > 0) {
                matchesCount.innerText = `${recs.length} matching jobs`;
                matchesList.innerHTML = recs.map(rec => `
                    <div class="match-list-item" onclick="window.location.hash='#jobDetails/${rec.job_id}'">
                        <div class="match-item-left">
                            <h4>${rec.job_title}</h4>
                            <span class="company">${rec.company}</span>
                            <div class="meta">
                                <span><i class="fa-solid fa-location-dot"></i> ${rec.location}</span>
                                <span><i class="fa-solid fa-money-bill-wave"></i> ${rec.salary || "Not Disclosed"}</span>
                            </div>
                        </div>
                        <div class="match-item-right">
                            <span class="match-badge ${rec.match_score >= 80 ? 'high' : ''}">${rec.match_score}%</span>
                            <span class="badge ${rec.match_score >= 80 ? 'badge-success' : 'badge-warning'}">Match</span>
                        </div>
                    </div>
                `).join("");

                const simJobSelect = document.getElementById("simulator-job-select");
                simJobSelect.innerHTML = `<option value="">-- Choose a target job --</option>` + recs.map(r => `
                    <option value="${r.job_id}">${r.job_title} (${r.company})</option>
                `).join("");
                
                document.getElementById("btn-simulate-gap").disabled = false;

            } else {
                matchesCount.innerText = "0 matches";
                matchesList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-folder-open"></i><p>No jobs matching your skills. Try optimizing keywords!</p></div>`;
            }
        } else {
            resumeEmpty.classList.remove("hidden");
            resumeDetails.classList.add("hidden");
            document.getElementById("kpi-ats-score").innerText = "N/A";
            document.getElementById("kpi-interview-score").innerText = "N/A";
            document.getElementById("kpi-github-score").innerText = "N/A";
            matchesList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-file-arrow-up"></i><p>Upload a resume first to fetch matching tech roles.</p></div>`;
        }
    } catch (err) {
        matchesList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><p>Error compiling dashboard statistics.</p></div>`;
    }
}

// 2. Explore Jobs list View Loader
async function loadJobsList() {
    const container = document.getElementById("jobs-view-list");
    container.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Loading matching jobs list...</p></div>`;

    try {
        const recs = await apiRequest("/api/recommendations/");
        if (recs && recs.length > 0) {
            container.innerHTML = recs.map(rec => `
                <div class="dashboard-card" style="cursor: pointer;" onclick="window.location.hash='#jobDetails/${rec.job_id}'">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <h3>${rec.job_title}</h3>
                            <p class="company-row" style="margin-top:4px;">
                                <span><i class="fa-solid fa-building"></i> ${rec.company}</span>
                                <span><i class="fa-solid fa-location-dot"></i> ${rec.location}</span>
                            </p>
                        </div>
                        <span class="match-badge ${rec.match_score >= 80 ? 'high' : ''}" style="font-size:1.5rem">${rec.match_score}% Match</span>
                    </div>
                    <div class="divider"></div>
                    <p style="font-size:0.85rem; color:var(--text-muted);">${rec.description.substring(0, 160)}...</p>
                    <div class="tag-cloud" style="margin-top:12px;">
                        ${rec.job_skills.slice(0, 5).map(s => {
                            const isMatched = !rec.missing_skills.includes(s);
                            return `<span class="${isMatched ? 'tag' : 'tag-missing'}">${s}</span>`;
                        }).join("")}
                    </div>
                </div>
            `).join("");
        } else {
            container.innerHTML = `
                <div class="dashboard-card text-center" style="grid-column: 1/-1;">
                    <i class="fa-solid fa-file-pdf" style="font-size:3rem; color:var(--border);"></i>
                    <h3 style="margin-top:16px;">No recommendations found</h3>
                    <p class="text-muted" style="margin-top:8px;">Ensure you have uploaded a resume file in the dashboard to scan and compare jobs.</p>
                </div>
            `;
        }
    } catch (err) {
        container.innerHTML = `<div class="dashboard-card text-center"><p>Error loading recommendation lists.</p></div>`;
    }
}

// 3. Job Details Loader
async function loadJobDetails(jobId) {
    try {
        const details = await apiRequest(`/api/job-success-probability/${jobId}`);
        const recs = await apiRequest("/api/recommendations/");
        const jobMatch = recs.find(r => r.job_id == jobId);

        if (!jobMatch) {
            showToast("Job match calculation error", "error");
            window.location.hash = "#jobs";
            return;
        }

        document.getElementById("jd-title").innerText = jobMatch.job_title;
        document.getElementById("jd-company").innerHTML = `<i class="fa-solid fa-building"></i> ${jobMatch.company}`;
        document.getElementById("jd-location").innerHTML = `<i class="fa-solid fa-location-dot"></i> ${jobMatch.location}`;
        document.getElementById("jd-salary").innerHTML = `<i class="fa-solid fa-money-bill-wave"></i> ${jobMatch.salary || "Not Disclosed"}`;
        document.getElementById("jd-description").innerText = jobMatch.description;

        document.getElementById("jd-match-percent").innerText = `${details.success_probability}%`;
        document.getElementById("jd-success-explanation").innerText = details.reasons.join(" ");

        const matched = jobMatch.job_skills.filter(s => !jobMatch.missing_skills.includes(s));
        document.getElementById("jd-matched-count").innerText = matched.length;
        document.getElementById("jd-matched-cloud").innerHTML = matched.map(s => `<span class="tag">${s}</span>`).join("");

        document.getElementById("jd-missing-count").innerText = jobMatch.missing_skills.length;
        document.getElementById("jd-missing-cloud").innerHTML = jobMatch.missing_skills.length > 0
            ? jobMatch.missing_skills.map(s => `<span class="tag-missing">${s}</span>`).join("")
            : `<span class="badge badge-success">Fully Ready! No Missing Skills.</span>`;

        const roadmapBtn = document.getElementById("btn-jd-roadmap");
        roadmapBtn.onclick = () => {
            window.location.hash = `#roadmap/${jobId}`;
        };

    } catch (err) {
        showToast("Error loading details for job.", "error");
    }
}

// 4. Learning Roadmap View Loader
async function loadRoadmap(jobId) {
    const journey = document.getElementById("roadmap-timeline-box");
    journey.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Compiling weekly roadmap steps...</p></div>`;

    try {
        let roadmapData;
        if (jobId) {
            roadmapData = await apiRequest(`/api/learning-paths/generate`, {
                method: "POST",
                body: { target_job: "" }
            });
            roadmapData = roadmapData.roadmap_data;
        } else {
            const hist = await apiRequest("/api/learning-paths/history");
            if (hist.length > 0) {
                roadmapData = hist[0].roadmap_data;
            }
        }

        if (roadmapData) {
            document.getElementById("rm-target-job").innerText = roadmapData.job_title;
            document.getElementById("rm-target-company").innerText = `Targeting skills for ${roadmapData.company}`;
            document.getElementById("rm-missing-skills-cloud").innerHTML = roadmapData.missing_skills.map(s => `<span class="tag-missing">${s}</span>`).join("");

            if (roadmapData.learning_path.length === 0) {
                journey.innerHTML = `
                    <div class="text-center" style="padding: 20px;">
                        <i class="fa-solid fa-circle-check" style="font-size:3rem; color:var(--success)"></i>
                        <h4 style="margin-top:16px;">You are fully optimized!</h4>
                        <p class="text-muted">No missing skills detected for this role.</p>
                    </div>
                `;
                return;
            }

            journey.innerHTML = roadmapData.learning_path.map((step, idx) => `
                <div class="roadmap-timeline-step">
                    <h4>Week ${idx + 1}: Acquire ${step.skill}</h4>
                    <ul>
                        <li><strong>Topics to Cover:</strong> ${step.topics.join(", ")}</li>
                        <li><strong>Curation Resources:</strong> ${step.resources.join(" | ")}</li>
                    </ul>
                    <div class="project-box">
                        <strong>Practical Task Milestone:</strong>
                        <p>${step.project}</p>
                    </div>
                </div>
            `).join("");
        } else {
            journey.innerHTML = `<div class="empty-state"><i class="fa-solid fa-route"></i><p>No active roadmap. Access a job detail view and click 'Generate Learning Path'.</p></div>`;
        }
    } catch (e) {
        journey.innerHTML = `<div class="empty-state"><i class="fa-solid fa-circle-exclamation icon-warning"></i><p>Upload a resume first to define missing competencies.</p></div>`;
    }
}

// 5. Mock Interview Loader
async function loadMockInterviewHistory() {
    const list = document.getElementById("interview-history-list");
    list.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Loading history...</p></div>`;

    try {
        const history = await apiRequest("/api/interview-prep/history");
        if (history.length > 0) {
            list.innerHTML = history.map(h => `
                <div class="history-item">
                    <div>
                        <span class="category">${h.category}</span>
                        <span class="text-muted" style="display:block; font-size:0.7rem;">${h.difficulty} | ${new Date(h.created_at).toLocaleDateString()}</span>
                    </div>
                    <span class="score">${h.score}%</span>
                </div>
            `).join("");

            const scores = history.slice().reverse().map(h => h.score);
            const labels = history.slice().reverse().map((h, i) => `Session ${i+1}`);
            
            drawChart("interviewTrendChart", "line", {
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Interview Scores',
                        data: scores,
                        borderColor: '#2563EB',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, max: 100 }
                    }
                }
            });
        } else {
            list.innerHTML = `<p class="text-muted">No completed attempts yet. Select config and click Start!</p>`;
        }
    } catch (err) {
        list.innerHTML = `<p class="text-muted">Error loading interview history logs.</p>`;
    }
}

// 6. Salary and trends view
async function loadSalaryAndTrends() {
    const timeline = document.getElementById("forecast-timeline-box");
    timeline.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Fetching trends data...</p></div>`;

    try {
        const trends = await apiRequest("/api/salary-prediction/trends");
        
        drawChart("marketDemandChart", "bar", {
            data: {
                labels: trends.demanded_skills.map(s => s.name),
                datasets: [{
                    label: 'Market Demand Share %',
                    data: trends.demanded_skills.map(s => s.percentage),
                    backgroundColor: '#3B82F6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        drawChart("highestPayingChart", "bar", {
            data: {
                labels: trends.highest_paying_skills.map(s => s.name),
                datasets: [{
                    label: 'Average Annual Salary ($)',
                    data: trends.highest_paying_skills.map(s => s.avg_salary),
                    backgroundColor: '#10B981',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        const career = await apiRequest("/api/career-path-predictor");
        timeline.innerHTML = career.timeline.map(step => `
            <div class="forecast-item">
                <h4>${step.term}</h4>
                <div class="role">${step.role}</div>
                <div class="sal">Salary target: ${step.expected_salary}</div>
                <div class="divider"></div>
                <p style="font-size:0.75rem; color:var(--text-muted);">Skills to acquire: ${step.skills_to_learn.join(", ")}</p>
                <p style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Responsibilities: ${step.responsibilities}</p>
            </div>
        `).join("");

    } catch (err) {
        timeline.innerHTML = `<p class="text-muted">Error loading career prediction forecast.</p>`;
    }
}

// 7. Load settings panel elements (Read-only Details, Notifications, Theme switcher)
async function loadSettings() {
    // 1. Load alerts preferences
    try {
        const alertSettings = await apiRequest("/api/job-alerts/settings");
        document.getElementById("setting-alert-frequency").value = alertSettings.frequency;
        document.getElementById("setting-notif-email").checked = alertSettings.email_notifications;
        document.getElementById("setting-notif-app").checked = alertSettings.in_app_notifications;
        document.getElementById("setting-target-role").value = alertSettings.preferences.target_role || "";
        document.getElementById("setting-target-location").value = alertSettings.preferences.location || "";
    } catch (err) {}

    // 2. Populate read-only account details from state (Name, Email, Role, Date)
    if (state.user) {
        document.getElementById("profile-detail-name").innerText = state.user.name || "Guest User";
        document.getElementById("profile-detail-email").innerText = state.user.email || "guest@example.com";
        document.getElementById("profile-detail-role").innerText = state.user.role || "Candidate";
        document.getElementById("profile-detail-date").innerText = state.user.created_at || "2026-06-25";
    }

    // 3. Sync dark theme toggle state
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    document.getElementById("setting-theme-toggle").checked = isDark;

    // 4. Fetch notification list inside settings right pane
    const list = document.getElementById("notifications-feed-list");
    const countBadge = document.getElementById("settings-notif-badge");
    list.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Syncing alerts...</p></div>`;

    try {
        const notifs = await apiRequest("/api/notifications");
        countBadge.innerText = `${notifs.length} Alerts`;
        
        if (notifs.length > 0) {
            list.innerHTML = notifs.map(n => `
                <div class="notif-item ${n.is_read ? '' : 'unread'}" id="notif-item-${n.id}">
                    <div class="icon">
                        <i class="fa-solid ${n.type === 'job_match' ? 'fa-briefcase' : n.type === 'alert' ? 'fa-triangle-exclamation' : 'fa-circle-info'}"></i>
                    </div>
                    <div class="text">
                        <div class="title">${n.title}</div>
                        <div class="msg">${n.message}</div>
                        <span class="time">${new Date(n.created_at).toLocaleDateString()}</span>
                    </div>
                    ${n.is_read ? '' : `<button class="read-btn" onclick="markNotificationRead(${n.id})">Mark read</button>`}
                </div>
            `).join("");
        } else {
            list.innerHTML = `<p class="text-muted">No notification alerts logs at the moment.</p>`;
        }
    } catch (err) {
        list.innerHTML = `<p class="text-muted">Error loading alerts.</p>`;
    }
}

// Mark notification read helper (triggered by window event)
window.markNotificationRead = async function(notifId) {
    try {
        await apiRequest(`/api/notifications/read/${notifId}`, { method: "POST" });
        const element = document.getElementById(`notif-item-${notifId}`);
        if (element) {
            element.classList.remove("unread");
            const btn = element.querySelector(".read-btn");
            if (btn) btn.remove();
        }
        showToast("Notification marked as read.", "success");
        loadDashboard();
        loadSettings();
    } catch (err) {}
};

// ==========================================================================
// AUTHENTICATION LOGOUT & UI WRAPPERS
// ==========================================================================

function handleLoginSuccess(token, userDetails, role = "job_seeker") {
    state.token = token;
    state.role = role;
    state.user = userDetails;
    
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
    localStorage.setItem("user", JSON.stringify(userDetails));

    updateUserWidgetUI();
    showToast("Signed in successfully!", "success");
    window.location.hash = "#dashboard";
}

function handleLogout() {
    state.token = null;
    state.role = null;
    state.user = null;
    
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user");

    showToast("Logged out successfully.", "info");
    window.location.hash = "#login";
}

function updateUserWidgetUI() {
    const nameLabel = document.getElementById("sidebar-user-name");
    const emailLabel = document.getElementById("sidebar-user-email");
    if (state.user) {
        nameLabel.innerText = state.user.name || "Active Candidate";
        emailLabel.innerText = state.user.email || "";
    } else {
        nameLabel.innerText = "Guest User";
        emailLabel.innerText = "guest@example.com";
    }
}

// ==========================================================================
// EVENT ATTACHMENTS & INTERACTIVE CONTROLLERS
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    
    router();
    window.addEventListener("hashchange", router);

    // Sidebar Collapsible Toggles
    const toggleInner = document.getElementById("sidebar-toggle-inner");
    const sidebar = document.getElementById("sidebar");
    toggleInner.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
    });

    // Mobile Hamburger
    const openBtn = document.getElementById("sidebar-open-btn");
    openBtn.addEventListener("click", () => {
        sidebar.classList.add("open");
    });

    // Sidebar logs & logout bindings
    document.getElementById("btn-sidebar-logout").addEventListener("click", handleLogout);

    // Dashboard redirects
    document.getElementById("btn-dash-upload-resume").addEventListener("click", () => {
        window.location.hash = "#upload";
    });

    // Settings Theme Preference switch
    const themeCheckbox = document.getElementById("setting-theme-toggle");
    themeCheckbox.addEventListener("change", () => {
        const activateDark = themeCheckbox.checked;
        const targetTheme = activateDark ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", targetTheme);
        showToast(`Theme switched to ${targetTheme} mode.`, "success");
    });

    // Settings Database Diagnostics checker
    document.getElementById("btn-check-db").addEventListener("click", async () => {
        const box = document.getElementById("db-check-results");
        box.innerText = "Running system inspection query...";
        box.classList.remove("hidden");

        try {
            const data = await apiRequest("/api/db-check");
            if (data && data.status === "connected") {
                box.innerHTML = `
                    <span style="color:var(--success)">Status: Connected</span><br>
                    Database: SQLite (Programmatic)<br>
                    Tables Count: ${data.tables.length}<br>
                    Tables list:<br>
                    ${data.tables.join(", ")}
                `;
                showToast("Database check completed.", "success");
            } else {
                box.innerHTML = `<span style="color:var(--error)">Status: Database Connection Error</span><br>${data ? data.error : "Unknown error"}`;
            }
        } catch (err) {
            box.innerHTML = `<span style="color:var(--error)">Diagnostics Request Failed</span>`;
        }
    });

    // Auth actions: Continue as Guest Click (Login view)
    document.getElementById("btn-login-guest").addEventListener("click", (e) => {
        e.preventDefault();
        handleLoginSuccess("guest-token", { 
            name: "Guest User", 
            email: "guest@example.com",
            role: "Candidate",
            created_at: new Date().toLocaleDateString()
        }, "job_seeker");
    });

    // Auth actions: Continue as Guest Click (Register view)
    document.getElementById("btn-register-guest").addEventListener("click", (e) => {
        e.preventDefault();
        handleLoginSuccess("guest-token", { 
            name: "Guest User", 
            email: "guest@example.com",
            role: "Candidate",
            created_at: new Date().toLocaleDateString()
        }, "job_seeker");
    });

    // Auth actions: Password Visibility Toggle Listener
    document.querySelectorAll(".toggle-password-visibility").forEach(eyeIcon => {
        eyeIcon.addEventListener("click", () => {
            const passwordInput = eyeIcon.previousElementSibling;
            if (passwordInput && passwordInput.tagName === "INPUT") {
                const currentType = passwordInput.getAttribute("type");
                const nextType = currentType === "password" ? "text" : "password";
                passwordInput.setAttribute("type", nextType);
                
                if (nextType === "text") {
                    eyeIcon.classList.remove("fa-eye");
                    eyeIcon.classList.add("fa-eye-slash");
                } else {
                    eyeIcon.classList.remove("fa-eye-slash");
                    eyeIcon.classList.add("fa-eye");
                }
            }
        });
    });

    // Auth actions: Login Form submission
    document.getElementById("form-login").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;

        try {
            const data = await apiRequest("/api/auth/login", {
                method: "POST",
                body: { email, password }
            });

            if (data && data.access_token) {
                const profile = await apiRequest("/api/auth/me", {
                    headers: { "Authorization": `Bearer ${data.access_token}` }
                });
                
                if (profile) {
                    const registrationDate = profile.created_at ? new Date(profile.created_at).toLocaleDateString() : new Date().toLocaleDateString();
                    handleLoginSuccess(data.access_token, { 
                        name: profile.name, 
                        email: profile.email,
                        role: profile.role === "job_seeker" ? "Candidate" : "Recruiter",
                        created_at: registrationDate
                    }, profile.role);
                }
            }
        } catch (e) {}
    });

    // Auth actions: Register Form submission
    document.getElementById("form-register").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("register-name").value;
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;

        if (password.length < 6) {
            showToast("Password must be at least 6 characters.", "error");
            return;
        }

        try {
            const data = await apiRequest("/api/auth/register", {
                method: "POST",
                body: { name, email, role: "job_seeker", password }
            });

            if (data) {
                showToast("Account created successfully! Please sign in.", "success");
                document.getElementById("login-email").value = email;
                window.location.hash = "#login";
            }
        } catch (err) {}
    });

    // Dashboard Simulator target job select checklist loader
    const simSelect = document.getElementById("simulator-job-select");
    simSelect.addEventListener("change", async () => {
        const jobId = simSelect.value;
        const checklist = document.getElementById("simulator-skills-checklist");
        
        if (!jobId) {
            checklist.innerHTML = "";
            return;
        }

        try {
            const recs = await apiRequest("/api/recommendations/");
            const match = recs.find(r => r.job_id == jobId);
            
            if (match && match.missing_skills.length > 0) {
                checklist.innerHTML = match.missing_skills.map(s => `
                    <label class="check-container">
                        <input type="checkbox" name="sim-skill" value="${s}">
                        <span>${s}</span>
                    </label>
                `).join("");
            } else {
                checklist.innerHTML = `<span class="text-success" style="font-size:0.8rem;"><i class="fa-solid fa-check"></i> Perfect match! No missing skills.</span>`;
            }
        } catch (err) {}
    });

    // Dashboard simulator submit button click
    document.getElementById("btn-simulate-gap").addEventListener("click", async () => {
        const jobId = simSelect.value;
        const checkboxes = document.querySelectorAll("input[name='sim-skill']:checked");
        const skillsToAdd = Array.from(checkboxes).map(cb => cb.value);

        if (!jobId) {
            showToast("Please choose a target job.", "error");
            return;
        }

        try {
            const sim = await apiRequest(`/api/skill-gap-simulator?job_id=${jobId}`, {
                method: "POST",
                body: skillsToAdd
            });
            
            document.getElementById("sim-score-before").innerText = `${sim.current_match_score}%`;
            document.getElementById("sim-score-after").innerText = `${sim.simulated_match_score}%`;
            document.getElementById("sim-feedback-text").innerText = `Acquiring these skills will yield a +${sim.gained_match}% match score improvement!`;
            document.getElementById("simulator-results-box").classList.remove("hidden");
            
            showToast("Skills simulated successfully!", "success");
        } catch (err) {}
    });

    // Resume vs JD Analyzer Fit Action
    document.getElementById("btn-analyze-jd").addEventListener("click", async () => {
        const jd = document.getElementById("analyzer-jd-input").value.trim();
        if (!jd) {
            showToast("Please paste the job description text.", "error");
            return;
        }

        const box = document.getElementById("analyzer-results-box");
        box.classList.add("hidden");

        try {
            const results = await apiRequest("/api/resume-optimizer/analyze-jd", {
                method: "POST",
                body: { job_description: jd }
            });

            document.getElementById("jd-anal-match-pct").innerText = `${results.match_percentage}%`;
            document.getElementById("jd-anal-compatibility-label").innerText = `ATS Score: ${results.ats_compatibility_score}%`;
            
            document.getElementById("jd-anal-matched-cloud").innerHTML = results.matched_skills.map(s => `<span class="tag">${s}</span>`).join("");
            document.getElementById("jd-anal-missing-cloud").innerHTML = results.missing_skills.length > 0 
                ? results.missing_skills.map(s => `<span class="tag-missing">${s}</span>`).join("")
                : `<span class="badge badge-success">No Missing Skills.</span>`;
            
            document.getElementById("jd-anal-suggestions").innerHTML = results.suggestions.map(s => `<li>${s}</li>`).join("");
            box.classList.remove("hidden");
            
            showToast("Job description analyzed.", "success");
        } catch (e) {}
    });

    // ----------------- Mock Interview Q&A Session Machine -----------------
    const activeSession = {
        category: null,
        difficulty: null,
        questions: [],
        answers: [],
        currentIndex: 0
    };

    document.getElementById("btn-start-interview").addEventListener("click", async () => {
        const category = document.getElementById("interview-category").value;
        const difficulty = document.getElementById("interview-difficulty").value;

        try {
            const data = await apiRequest("/api/interview-prep/questions", {
                method: "POST",
                body: { category, difficulty }
            });

            activeSession.category = category;
            activeSession.difficulty = difficulty;
            activeSession.questions = data.questions;
            activeSession.answers = [];
            activeSession.currentIndex = 0;

            document.getElementById("int-setup-card").classList.add("hidden");
            document.getElementById("int-feedback-card").classList.add("hidden");
            document.getElementById("int-session-card").classList.remove("hidden");

            renderActiveQuestion();
            showToast("Mock interview started. Write complete answers.", "success");
        } catch (e) {}
    });

    function renderActiveQuestion() {
        const chatBox = document.getElementById("interview-chat-box");
        const idx = activeSession.currentIndex;
        const question = activeSession.questions[idx];

        document.getElementById("session-progress-badge").innerText = `Question ${idx + 1} of ${activeSession.questions.length}`;
        
        chatBox.innerHTML = `
            <div class="assistant-bubble">
                <p><strong>[Question ${idx + 1}]:</strong> ${question}</p>
            </div>
        `;
        document.getElementById("interview-answer-input").value = "";
    }

    document.getElementById("btn-submit-answer").addEventListener("click", async () => {
        const answer = document.getElementById("interview-answer-input").value.trim();
        if (!answer) {
            showToast("Please enter an answer to proceed.", "error");
            return;
        }

        activeSession.answers.push(answer);
        activeSession.currentIndex += 1;

        if (activeSession.currentIndex < activeSession.questions.length) {
            renderActiveQuestion();
        } else {
            showToast("Evaluation in progress. Calculating competency scores...", "info");
            
            try {
                const result = await apiRequest("/api/interview-prep/submit", {
                    method: "POST",
                    body: {
                        category: activeSession.category,
                        difficulty: activeSession.difficulty,
                        questions: activeSession.questions,
                        answers: activeSession.answers
                    }
                });

                document.getElementById("int-session-card").classList.add("hidden");
                document.getElementById("int-feedback-card").classList.remove("hidden");

                document.getElementById("feedback-score-num").innerText = `${result.score}%`;
                document.getElementById("feedback-rating").innerText = result.feedback.overall_feedback;
                
                document.getElementById("feedback-breakdowns-list").innerHTML = result.feedback.question_breakdowns.map((bd, i) => `
                    <div style="margin-top: 14px;">
                        <strong>Q${i+1}: ${bd.question}</strong>
                        <p class="text-muted" style="font-size:0.8rem; margin-top:2px;">Your Answer: "${activeSession.answers[i]}"</p>
                        <p class="sim-feedback" style="text-align:left; font-size:0.8rem; color:var(--primary); margin-top:4px;">Score: ${bd.score}% | ${bd.feedback}</p>
                    </div>
                `).join("");

                loadMockInterviewHistory();
                loadDashboard();
            } catch (err) {}
        }
    });

    document.getElementById("btn-restart-interview").addEventListener("click", () => {
        document.getElementById("int-feedback-card").classList.add("hidden");
        document.getElementById("int-setup-card").classList.remove("hidden");
    });

    // ----------------- GitHub Analyzer Submission -----------------
    document.getElementById("btn-analyze-github").addEventListener("click", async () => {
        const username = document.getElementById("github-username-input").value.trim();
        if (!username) {
            showToast("Please enter a username.", "error");
            return;
        }

        showToast("Accessing public API... Simulating repository code logs", "info");

        try {
            const data = await apiRequest("/api/github-analyzer/analyze", {
                method: "POST",
                body: { username }
            });
            const stats = data.profile_data;

            document.getElementById("git-repos-count").innerText = stats.repos_count;
            document.getElementById("git-stars-count").innerText = stats.stars;
            document.getElementById("git-followers-count").innerText = stats.followers;
            document.getElementById("git-readiness-val").innerText = `${stats.hiring_readiness}%`;
            document.getElementById("git-portfolio-val").innerText = `${stats.portfolio_score}%`;

            document.getElementById("git-repos-list").innerHTML = stats.top_repos.map(r => `
                <div class="repo-card">
                    <h5>
                        <strong>${r.name}</strong>
                        <span><i class="fa-solid fa-star"></i> ${r.stars}</span>
                    </h5>
                    <p>${r.description}</p>
                </div>
            `).join("");

            document.getElementById("git-suggestions-list").innerHTML = stats.suggestions.map(s => `<li>${s}</li>`).join("");

            const langLabels = Object.keys(stats.top_languages);
            const langValues = Object.values(stats.top_languages);

            drawChart("githubLanguagesChart", "pie", {
                data: {
                    labels: langLabels,
                    datasets: [{
                        data: langValues,
                        backgroundColor: ['#2563EB', '#10B981', '#F59E0B', '#3B82F6', '#64748B']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });

            document.getElementById("github-results-container").classList.remove("hidden");
            showToast("GitHub profile parsed successfully.", "success");
            loadDashboard();
        } catch (e) {}
    });

    // ----------------- Salary Predictor Calculator -----------------
    document.getElementById("btn-predict-salary").addEventListener("click", async () => {
        const skillsText = document.getElementById("salary-skills-input").value.trim();
        const experience = parseInt(document.getElementById("salary-experience-input").value) || 0;
        const location = document.getElementById("salary-location-input").value.trim();

        if (!skillsText) {
            showToast("Please provide skills.", "error");
            return;
        }

        const skills = skillsText.split(",").map(s => s.trim()).filter(s => s);

        try {
            const pred = await apiRequest("/api/salary-prediction/predict", {
                method: "POST",
                body: { skills, experience, location }
            });

            document.getElementById("sal-min-val").innerText = `$${pred.min_salary.toLocaleString()}`;
            document.getElementById("sal-avg-val").innerText = `$${pred.avg_salary.toLocaleString()}`;
            document.getElementById("sal-max-val").innerText = `$${pred.max_salary.toLocaleString()}`;
            document.getElementById("sal-confidence-val").innerText = `${Math.round(pred.confidence_score * 100)}%`;

            document.getElementById("salary-output-box").classList.remove("hidden");
            showToast("Salary estimate calculated.", "success");
        } catch (err) {}
    });

    // ----------------- Save Alerts Settings Actions -----------------
    document.getElementById("btn-save-settings").addEventListener("click", async () => {
        const frequency = document.getElementById("setting-alert-frequency").value;
        const email_notifications = document.getElementById("setting-notif-email").checked;
        const in_app_notifications = document.getElementById("setting-notif-app").checked;
        const target_role = document.getElementById("setting-target-role").value.trim();
        const location = document.getElementById("setting-target-location").value.trim();

        try {
            await apiRequest("/api/job-alerts/settings", {
                method: "POST",
                body: {
                    frequency,
                    email_notifications,
                    in_app_notifications,
                    preferences: { target_role, location }
                }
            });
            showToast("Alert preferences saved.", "success");
        } catch (e) {}
    });

    // ----------------- File Upload drag zone actions -----------------
    let fileToUpload = null;
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("resume-file-input");
    const processBtn = document.getElementById("btn-process-resume");
    const selectedFileLabel = document.getElementById("selected-file-name");

    dropZone.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });
    
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    function handleFileSelect(file) {
        const nameLower = file.name.toLowerCase();
        if (!nameLower.endsWith(".pdf") && !nameLower.endsWith(".docx")) {
            showToast("Select a PDF or DOCX file.", "error");
            resetUpload();
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            showToast("Max file size limit is 5MB.", "error");
            resetUpload();
            return;
        }

        fileToUpload = file;
        selectedFileLabel.innerText = `File: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
        selectedFileLabel.classList.remove("hidden");
        processBtn.disabled = false;
    }

    function resetUpload() {
        fileToUpload = null;
        selectedFileLabel.classList.add("hidden");
        processBtn.disabled = true;
        document.getElementById("upload-progress-container").classList.add("hidden");
        document.getElementById("upload-progress-bar").style.width = "0%";
    }

    processBtn.addEventListener("click", () => {
        if (!fileToUpload) return;

        const formData = new FormData();
        formData.append("file", fileToUpload);

        const progressContainer = document.getElementById("upload-progress-container");
        const progressBar = document.getElementById("upload-progress-bar");
        const progressText = document.getElementById("upload-status-text");

        progressContainer.classList.remove("hidden");
        processBtn.disabled = true;

        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API_BASE}/api/resumes/upload`);
        
        if (state.token) {
            xhr.setRequestHeader("Authorization", `Bearer ${state.token}`);
        }

        xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = `${percent}%`;
                progressText.innerText = `Uploading resume... ${percent}%`;
                if (percent === 100) {
                    progressText.innerText = "Extracting skills and generating AI metrics...";
                }
            }
        });

        xhr.onload = () => {
            if (xhr.status === 200 || xhr.status === 201) {
                showToast("Resume parsed and matched successfully!", "success");
                resetUpload();
                setTimeout(() => {
                    window.location.hash = "#dashboard";
                }, 1000);
            } else {
                let err = "Processing failed.";
                try {
                    const parsed = JSON.parse(xhr.responseText);
                    err = parsed.detail || err;
                } catch (e) {}
                showToast(err, "error");
                resetUpload();
            }
        };

        xhr.onerror = () => {
            showToast("Network connection error.", "error");
            resetUpload();
        };

        xhr.send(formData);
    });
});
