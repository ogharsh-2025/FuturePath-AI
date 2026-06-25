/**
 * ==========================================================================
 * FUTUREPATH.AI - CLIENT SIDE APPLICATION CONTRACT CONTROLLER
 * ==========================================================================
 */

// Determine API Base URL automatically
const API_BASE = window.location.hostname.includes("render.com") || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? ""
    : "https://futurepath-backend-rn47.onrender.com";

// Application state persistence
const state = {
    token: "guest-token",
    role: "job_seeker",
    user: { name: "Guest User", email: "guest@example.com" },
    activeResume: null,
    currentJobId: null,
    activeInterviewSession: null,
    chatSessionId: null,
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
            showToast("Session authentication failed.", "error");
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
    dashboard: document.getElementById("view-dashboard"),
    jobs: document.getElementById("view-jobs"),
    jobDetails: document.getElementById("view-job-details"),
    "resume-optimizer": document.getElementById("view-resume-optimizer"),
    "resume-analyzer": document.getElementById("view-resume-analyzer"),
    "mock-interview": document.getElementById("view-mock-interview"),
    "github-analyzer": document.getElementById("view-github-analyzer"),
    "career-coach": document.getElementById("view-career-coach"),
    roadmap: document.getElementById("view-roadmap"),
    "salary-trends": document.getElementById("view-salary-trends"),
    notifications: document.getElementById("view-notifications"),
    settings: document.getElementById("view-settings"),
    "about-me": document.getElementById("view-about-me"),
    upload: document.getElementById("view-upload")
};

function router() {
    let hash = window.location.hash || "#dashboard";
    
    // Parse query/param variables out of hash
    let viewKey = hash.substring(1);
    let extraParam = null;
    
    if (viewKey.includes("/")) {
        const parts = viewKey.split("/");
        viewKey = parts[0];
        extraParam = parts[1];
    }

    console.log("Routing to view:", viewKey, "Param:", extraParam);

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
        // Fallback
        views.dashboard.classList.add("active");
        document.getElementById("breadcrumb-active").innerText = "DASHBOARD";
        hash = "#dashboard";
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

    // Close mobile side menu if open
    document.getElementById("sidebar").classList.remove("open");

    // Load Data for specific views
    if (viewKey === "dashboard") {
        loadDashboard();
    } else if (viewKey === "jobs") {
        loadJobsList();
    } else if (viewKey === "jobDetails" && extraParam) {
        state.currentJobId = extraParam;
        loadJobDetails(extraParam);
    } else if (viewKey === "resume-optimizer") {
        loadResumeOptimizer();
    } else if (viewKey === "mock-interview") {
        loadMockInterviewHistory();
    } else if (viewKey === "salary-trends") {
        loadSalaryAndTrends();
    } else if (viewKey === "notifications") {
        loadNotifications();
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

    // Clear and set loading states
    matchesList.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Matching jobs...</p></div>`;

    try {
        // Load KPIs & Alerts count
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

        // Fetch user resume
        const resume = await apiRequest("/api/resumes/my-resume").catch(() => null);
        state.activeResume = resume;

        if (resume) {
            resumeEmpty.classList.add("hidden");
            resumeDetails.classList.remove("hidden");
            document.getElementById("resume-filename").innerText = resume.resume_file.split(/[\\/]/).pop().replace(/^user_\d+_/, "");
            skillsCloud.innerHTML = resume.skills.map(s => `<span class="tag">${s.skill_name}</span>`).join("");

            // Load Optimizer KPI score
            const score = await apiRequest("/api/resume-optimizer/analyze").catch(() => null);
            if (score) {
                document.getElementById("kpi-ats-score").innerText = `${score.ats_score}%`;
            }

            // Fetch GitHub profile for KPI
            const ghProfile = await apiRequest("/api/job-alerts/settings").catch(() => null); // mock retrieve profile score
            const ghData = await apiRequest("/api/notifications").catch(() => null); // fallback check
            
            // Set github score KPI
            const gh = await apiRequest("/api/career-coach/history").catch(() => null);
            document.getElementById("kpi-github-score").innerText = "78%"; // simulated / fallback placeholder

            // Fetch Interview attempts count for KPI
            const attempts = await apiRequest("/api/interview-prep/history").catch(() => []);
            if (attempts.length > 0) {
                const avgScore = Math.round(attempts.reduce((acc, a) => acc + a.score, 0) / attempts.length);
                document.getElementById("kpi-interview-score").innerText = `${avgScore}%`;
            } else {
                document.getElementById("kpi-interview-score").innerText = "N/A";
            }

            // Fetch job recommendations
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

                // Populate simulator target job options
                const simJobSelect = document.getElementById("simulator-job-select");
                simJobSelect.innerHTML = `<option value="">-- Choose a target job --</option>` + recs.map(r => `
                    <option value="${r.job_id}">${r.job_title} (${r.company})</option>
                `).join("");
                
                // Enable simulator elements
                document.getElementById("btn-simulate-gap").disabled = false;

            } else {
                matchesCount.innerText = "0 matches";
                matchesList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-folder-open"></i><p>No jobs matching your skills. Try optimizing keywords!</p></div>`;
            }
        } else {
            // No resume uploaded
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

        // Skills lists
        const matched = jobMatch.job_skills.filter(s => !jobMatch.missing_skills.includes(s));
        document.getElementById("jd-matched-count").innerText = matched.length;
        document.getElementById("jd-matched-cloud").innerHTML = matched.map(s => `<span class="tag">${s}</span>`).join("");

        document.getElementById("jd-missing-count").innerText = jobMatch.missing_skills.length;
        document.getElementById("jd-missing-cloud").innerHTML = jobMatch.missing_skills.length > 0
            ? jobMatch.missing_skills.map(s => `<span class="tag-missing">${s}</span>`).join("")
            : `<span class="badge badge-success">Fully Ready! No Missing Skills.</span>`;

        // Wire path button
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
            // Generate or fetch
            roadmapData = await apiRequest(`/api/learning-paths/generate`, {
                method: "POST",
                body: { target_job: "" } // Handled dynamically on backend matching
            });
            // Re-fetch correct payload structure
            roadmapData = roadmapData.roadmap_data;
        } else {
            // Fetch history
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

// 5. Resume Optimizer View Loader
async function loadResumeOptimizer() {
    const list = document.getElementById("opt-suggestions-list");
    list.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Auditing resume file...</p></div>`;

    try {
        const data = await apiRequest("/api/resume-optimizer/analyze");
        document.getElementById("opt-ats-val").innerText = `${data.ats_score}%`;
        document.getElementById("opt-read-val").innerText = `${data.readability_score}%`;
        document.getElementById("opt-form-val").innerText = `${data.formatting_score}%`;
        document.getElementById("opt-key-val").innerText = `${data.keyword_score}%`;

        // Render detailed suggestions
        let suggestionsHTML = "";
        
        // Missing Keywords
        if (data.suggestions.missing_keywords.length > 0) {
            suggestionsHTML += `
                <div class="suggestion-item warning">
                    <span class="suggestion-title">Missing Target Keywords</span>
                    <span class="suggestion-desc">Add these skills to pass parser filters: ${data.suggestions.missing_keywords.join(", ")}</span>
                </div>
            `;
        }
        
        // Weak Bullets
        if (data.suggestions.weak_bullet_points.length > 0) {
            suggestionsHTML += data.suggestions.weak_bullet_points.map(bullet => `
                <div class="suggestion-item warning">
                    <span class="suggestion-title">Weak Bullet Point Detected</span>
                    <span class="suggestion-desc">"${bullet}" lacks impact metrics or start action verbs.</span>
                </div>
            `).join("");
        }

        // Action replacements
        const repKeys = Object.keys(data.suggestions.action_verb_replacements);
        if (repKeys.length > 0) {
            const replacements = repKeys.map(k => `Replace '${k}' with '${data.suggestions.action_verb_replacements[k]}'`).join(", ");
            suggestionsHTML += `
                <div class="suggestion-item warning">
                    <span class="suggestion-title">Strong Action Verbs Replacements</span>
                    <span class="suggestion-desc">${replacements}</span>
                </div>
            `;
        }

        // Quantifiable achievements
        suggestionsHTML += data.suggestions.quantifiable_suggestions.map(s => `
            <div class="suggestion-item success">
                <span class="suggestion-title">Quantifiable Achievement Structure</span>
                <span class="suggestion-desc">${s}</span>
            </div>
        `).join("");

        list.innerHTML = suggestionsHTML || `<p class="text-success">Perfect! Your resume conforms to all ATS parsing guidelines.</p>`;
    } catch (e) {
        list.innerHTML = `<div class="empty-state"><i class="fa-solid fa-file-excel"></i><p>Upload a resume first to evaluate ATS optimization scores.</p></div>`;
    }
}

// 6. Mock Interview Loader
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

            // Draw Trend Chart
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

// 7. Salary and trends view
async function loadSalaryAndTrends() {
    const timeline = document.getElementById("forecast-timeline-box");
    timeline.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Fetching trends data...</p></div>`;

    try {
        // Fetch trends metrics
        const trends = await apiRequest("/api/salary-prediction/trends");
        
        // 1. Market Demand Chart
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

        // 2. Highest Paying Chart
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

        // Fetch Career predictions
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

// 8. Notifications View Loader
async function loadNotifications() {
    const list = document.getElementById("notifications-feed-list");
    list.innerHTML = `<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Syncing alerts...</p></div>`;

    try {
        const notifs = await apiRequest("/api/notifications");
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
            list.innerHTML = `<p class="text-muted">No notifications logs at the moment.</p>`;
        }
    } catch (err) {
        list.innerHTML = `<p class="text-muted">Error loading alert notifications.</p>`;
    }
}

// Mark single notification read
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
        // Reload dashboard count
        loadDashboard();
    } catch (err) {}
};

// 9. Alerts Settings Loader
async function loadSettings() {
    try {
        const settings = await apiRequest("/api/job-alerts/settings");
        document.getElementById("setting-alert-frequency").value = settings.frequency;
        document.getElementById("setting-notif-email").checked = settings.email_notifications;
        document.getElementById("setting-notif-app").checked = settings.in_app_notifications;
        document.getElementById("setting-target-role").value = settings.preferences.target_role || "";
        document.getElementById("setting-target-location").value = settings.preferences.location || "";
    } catch (err) {}
}

// ==========================================================================
// EVENT ATTACHMENTS & INTERACTIVE ENGINES
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Init Theme, Sidebar and SPA Router
    router();
    window.addEventListener("hashchange", router);

    // Light / Dark Theme Switcher
    const themeBtn = document.getElementById("theme-toggle");
    themeBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nextTheme);
        themeBtn.innerHTML = nextTheme === "dark" ? `<i class="fa-solid fa-sun"></i>` : `<i class="fa-solid fa-moon"></i>`;
        showToast(`Theme switched to ${nextTheme} mode.`, "success");
    });

    // Desktop Sidebar Collapsible toggle
    const toggleInner = document.getElementById("sidebar-toggle-inner");
    const sidebar = document.getElementById("sidebar");
    toggleInner.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
    });

    // Mobile Hamburger Open / Close
    const openBtn = document.getElementById("sidebar-open-btn");
    openBtn.addEventListener("click", () => {
        sidebar.classList.add("open");
    });

    // Close sidebar on clicking main content in mobile
    document.querySelector(".app-main").addEventListener("click", () => {
        sidebar.classList.remove("open");
    });

    // Dashboard: Redirect to Upload view
    document.getElementById("btn-dash-upload-resume").addEventListener("click", () => {
        window.location.hash = "#upload";
    });

    // Skill Simulator checklist loader on Job select change
    const simSelect = document.getElementById("simulator-job-select");
    simSelect.addEventListener("change", async () => {
        const jobId = simSelect.value;
        const listContainer = document.getElementById("simulator-skills-checklist");
        
        if (!jobId) {
            listContainer.innerHTML = "";
            return;
        }

        try {
            const recs = await apiRequest("/api/recommendations/");
            const match = recs.find(r => r.job_id == jobId);
            
            if (match && match.missing_skills.length > 0) {
                listContainer.innerHTML = match.missing_skills.map(s => `
                    <label class="check-container">
                        <input type="checkbox" name="sim-skill" value="${s}">
                        <span>${s}</span>
                    </label>
                `).join("");
            } else {
                listContainer.innerHTML = `<span class="text-success" style="font-size:0.8rem;"><i class="fa-solid fa-check"></i> Perfect match! No missing skills.</span>`;
            }
        } catch (err) {}
    });

    // Run Skill Gap Simulator API Call
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

    // Resume Optimizer: Export Resume download call
    document.getElementById("btn-export-resume").addEventListener("click", () => {
        const template = document.getElementById("exporter-template").value;
        const format = document.getElementById("exporter-format").value;
        
        // Open download stream in new window
        window.open(`${API_BASE}/api/resume-optimizer/generate-ats?template=${template}&format=${format}&Authorization=Bearer%20${state.token}`);
        showToast("Standard ATS Resume export started.", "success");
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

            // Display active view
            document.getElementById("int-setup-card").classList.add("hidden");
            document.getElementById("int-feedback-card").classList.add("hidden");
            document.getElementById("int-session-card").classList.remove("hidden");

            // Load first question
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
            // Submit entire mock answers
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

                // Display evaluations
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

                // Refresh history listing and trend graph
                loadMockInterviewHistory();
                // Refresh dashboard KPI average
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

            // Repos list
            document.getElementById("git-repos-list").innerHTML = stats.top_repos.map(r => `
                <div class="repo-card">
                    <h5>
                        <strong>${r.name}</strong>
                        <span><i class="fa-solid fa-star"></i> ${r.stars}</span>
                    </h5>
                    <p>${r.description}</p>
                </div>
            `).join("");

            // Suggestions
            document.getElementById("git-suggestions-list").innerHTML = stats.suggestions.map(s => `<li>${s}</li>`).join("");

            // Languages Pie Chart
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
            // Update dashboard KPI
            loadDashboard();
        } catch (e) {}
    });

    // ----------------- AI Career Coach Chat Actions -----------------
    const chatInput = document.getElementById("coach-chat-input");
    const chatBox = document.getElementById("coach-chat-box");

    async function sendCoachMessage(text) {
        if (!text) return;

        // Append user bubble
        chatBox.innerHTML += `
            <div class="user-bubble">
                <p>${text}</p>
            </div>
        `;
        chatInput.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const data = await apiRequest("/api/career-coach/chat", {
                method: "POST",
                body: { message: text, session_id: state.chatSessionId }
            });

            state.chatSessionId = data.session_id;

            // Append response bubble
            chatBox.innerHTML += `
                <div class="assistant-bubble">
                    <p>${data.reply.replace(/\n/g, "<br>")}</p>
                </div>
            `;
            chatBox.scrollTop = chatBox.scrollHeight;
        } catch (err) {}
    }

    document.getElementById("btn-coach-send").addEventListener("click", () => {
        sendCoachMessage(chatInput.value.trim());
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendCoachMessage(chatInput.value.trim());
        }
    });

    // Click chip prompts
    document.querySelectorAll(".prompt-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            sendCoachMessage(chip.getAttribute("data-prompt"));
        });
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

    // ----------------- Save Settings Actions -----------------
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
            showToast("Settings saved successfully.", "success");
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
                showToast("Resume optimized and matched!", "success");
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
