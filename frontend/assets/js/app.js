/**
 * ==========================================================================
 * FUTUREPATH.AI - CLIENT SIDE APPLICATION SCRIPT
 * ==========================================================================
 */

// API Base URL config (Relative path works because FastAPI hosts the folder)
const API_BASE = "";

// Global State
const state = {
    token: localStorage.getItem("token") || null,
    role: localStorage.getItem("role") || null, // job_seeker or recruiter
    user: null,
    currentJobId: null
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

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// ==========================================================================
// HTTP Client Wrapper with Auth Headers
// ==========================================================================
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    // Inject headers
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
        
        // Handle 401 Unauthorized
        if (response.status === 401 && state.token) {
            handleLogout();
            showToast("Session expired. Please log in again.", "error");
            return null;
        }

        // Return empty on 204 No Content
        if (response.status === 204) {
            return true;
        }

        let data = null;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            try {
                data = await response.json();
            } catch (jsonErr) {
                const text = await response.text();
                throw new Error(text || "Invalid JSON response from server");
            }
        } else {
            const text = await response.text();
            if (!response.ok) {
                throw new Error(text || `Request failed with status ${response.status}`);
            }
            return text;
        }

        if (!response.ok) {
            throw new Error((data && data.detail) || "Something went wrong");
        }
        return data;
    } catch (error) {
        console.error("API Error:", error.message);
        showToast(error.message, "error");
        throw error;
    }
}

// ==========================================================================
// SPA ROUTER
// ==========================================================================
const views = {
    home: document.getElementById("view-home"),
    auth: document.getElementById("view-auth"),
    dashboard: document.getElementById("view-dashboard"),
    recruiter: document.getElementById("view-recruiter"),
    upload: document.getElementById("view-upload"),
    jobDetails: document.getElementById("view-job-details"),
    roadmap: document.getElementById("view-roadmap")
};

function router() {
    const hash = window.location.hash || "#home";
    console.log("Navigating to:", hash);

    // Hide all views first by removing the active class
    Object.values(views).forEach(view => {
        if (view) view.classList.remove("active");
    });
    
    // De-activate all nav links
    document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));

    // Handle Routes
    if (hash === "#home") {
        views.home.classList.add("active");
        document.getElementById("nav-home").classList.add("active");
    } 
    else if (hash === "#login" || hash === "#register") {
        views.auth.classList.add("active");
        toggleAuthForms(hash === "#register");
    } 
    else if (hash === "#dashboard") {
        if (!checkAuth()) return;
        views.dashboard.classList.add("active");
        document.getElementById("nav-dashboard").classList.add("active");
        loadDashboardData();
    } 
    else if (hash === "#recruiter") {
        if (!checkAuth() || !checkRole("recruiter")) return;
        views.recruiter.classList.add("active");
        document.getElementById("nav-recruiter").classList.add("active");
        loadRecruiterData();
    } 
    else if (hash === "#upload") {
        if (!checkAuth()) return;
        views.upload.classList.add("active");
        document.getElementById("nav-upload").classList.add("active");
        resetUploadForm();
    } 
    else if (hash.startsWith("#job/")) {
        if (!checkAuth()) return;
        const jobId = hash.split("/")[1];
        state.currentJobId = jobId;
        views.jobDetails.classList.add("active");
        loadJobDetails(jobId);
    } 
    else if (hash.startsWith("#roadmap/")) {
        if (!checkAuth()) return;
        const jobId = hash.split("/")[1];
        views.roadmap.classList.add("active");
        loadRoadmap(jobId);
    } 
    else {
        // Fallback to home
        window.location.hash = "#home";
    }
}

// Check if user is logged in
function checkAuth() {
    if (!state.token) {
        window.location.hash = "#login";
        showToast("Please login to access this page", "error");
        return false;
    }
    return true;
}

// Check if user has required role
function checkRole(requiredRole) {
    if (state.role !== requiredRole) {
        window.location.hash = "#dashboard";
        showToast("Unauthorized access", "error");
        return false;
    }
    return true;
}

// Update Nav Buttons based on logged in status
function updateNavUI() {
    const isLoggedIn = !!state.token;
    
    // Toggle login/logout button
    if (isLoggedIn) {
        document.getElementById("btn-login-nav").classList.add("hidden");
        document.getElementById("btn-logout-nav").classList.remove("hidden");
        
        // Show auth-only links depending on role
        document.querySelectorAll(".auth-required").forEach(el => el.classList.remove("hidden"));
        if (state.role === "recruiter") {
            document.getElementById("nav-dashboard").classList.add("hidden");
        } else {
            document.getElementById("nav-recruiter").classList.add("hidden");
        }
    } else {
        document.getElementById("btn-login-nav").classList.remove("hidden");
        document.getElementById("btn-logout-nav").classList.add("hidden");
        document.querySelectorAll(".auth-required").forEach(el => el.classList.add("hidden"));
    }
}

// Toggle between Login and Register Cards in the Auth view
function toggleAuthForms(showRegister) {
    const loginCard = document.getElementById("login-card");
    const registerCard = document.getElementById("register-card");
    if (showRegister) {
        loginCard.classList.add("hidden");
        registerCard.classList.remove("hidden");
    } else {
        loginCard.classList.remove("hidden");
        registerCard.classList.add("hidden");
    }
}

// Log in
function handleLoginSuccess(token, role) {
    state.token = token;
    state.role = role;
    localStorage.setItem("token", token);
    localStorage.setItem("role", role);
    
    updateNavUI();
    showToast("Signed in successfully!", "success");
    
    if (role === "recruiter") {
        window.location.hash = "#recruiter";
    } else {
        window.location.hash = "#dashboard";
    }
}

// Log out
function handleLogout() {
    state.token = null;
    state.role = null;
    state.user = null;
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    
    updateNavUI();
    window.location.hash = "#home";
    showToast("Logged out successfully.", "info");
}

// ==========================================================================
// SERVICE CALLS & DATA RETRIEVAL
// ==========================================================================

// --- Candidate Dashboard Loading ---
async function loadDashboardData() {
    const resumeContainer = document.getElementById("resume-status-container");
    const recsContainer = document.getElementById("recommendations-container");
    const matchesBadge = document.getElementById("matches-count-badge");
    
    try {
        // 1. Fetch Resume Status
        const resume = await apiRequest("/api/resumes/my-resume");
        
        if (resume) {
            // Render Resume Profile details
            const skillsBadges = resume.skills.map(s => `<span class="tag">${s.skill_name}</span>`).join("");
            resumeContainer.innerHTML = `
                <div class="resume-active-state">
                    <div class="badge badge-success"><i class="fa-solid fa-file-circle-check"></i> Active Resume</div>
                    <div class="resume-meta-info">
                        <div><span>File:</span> ${resume.resume_file.split(/[\\/]/).pop().replace(/^user_\d+_/, "")}</div>
                        <div><span>Uploaded:</span> ${new Date(resume.created_at).toLocaleDateString()}</div>
                    </div>
                    <div class="resume-skills-pane">
                        <h4>Extracted Skills:</h4>
                        <div class="skill-tags-group">${skillsBadges || '<span class="color-text-muted">None detected</span>'}</div>
                    </div>
                    <button id="btn-reupload" class="btn btn-secondary">Upload New File</button>
                </div>
            `;
            // Reupload handler
            document.getElementById("btn-reupload").addEventListener("click", () => {
                window.location.hash = "#upload";
            });

            // 2. Fetch Job Matches
            recsContainer.innerHTML = `
                <div class="loading-state">
                    <i class="fa-solid fa-circle-notch fa-spin spinner"></i>
                    <p>Comparing your resume vector against job bank postings...</p>
                </div>
            `;
            const recs = await apiRequest("/api/recommendations/");
            
            if (recs && recs.length > 0) {
                matchesBadge.innerText = `${recs.length} matches`;
                matchesBadge.className = "badge badge-success";
                
                recsContainer.innerHTML = recs.map(rec => {
                    const isHigh = rec.match_score >= 80;
                    const missingBadges = rec.missing_skills.length > 0 
                        ? rec.missing_skills.slice(0, 3).map(s => `<span class="tag-missing">${s}</span>`).join(" ") + (rec.missing_skills.length > 3 ? "..." : "")
                        : "None (Perfect skill fit!)";
                        
                    return `
                        <div class="glass-card job-match-card ${isHigh ? 'high-match' : ''}" onclick="window.location.hash = '#job/${rec.job_id}'">
                            <div class="job-card-header">
                                <div>
                                    <h3>${rec.job_title}</h3>
                                    <div class="company-meta">${rec.company}</div>
                                </div>
                                <span class="match-score-pill">${rec.match_score}% Match</span>
                            </div>
                            <div class="job-card-details-row">
                                <span><i class="fa-solid fa-location-dot"></i> ${rec.location}</span>
                                <span><i class="fa-solid fa-money-bill-wave"></i> ${rec.salary || "Not Disclosed"}</span>
                            </div>
                            <div class="card-missing-skills">
                                <label>Missing Requirements:</label>
                                <div class="skill-tags" style="margin-top: 6px;">${missingBadges}</div>
                            </div>
                        </div>
                    `;
                }).join("");
            } else {
                matchesBadge.innerText = "0 matches";
                matchesBadge.className = "badge badge-warning-count";
                recsContainer.innerHTML = `
                    <div class="no-resume-state">
                        <i class="fa-solid fa-circle-info icon-warning"></i>
                        <p>No job postings match your resume currently. Recruiters are adding more postings daily!</p>
                    </div>
                `;
            }

        } else {
            // Render upload prompt state
            renderNoResumeState(resumeContainer, recsContainer, matchesBadge);
        }
    } catch (e) {
        // If resume is missing (404), render upload prompt state
        renderNoResumeState(resumeContainer, recsContainer, matchesBadge);
    }
}

function renderNoResumeState(resumeEl, recsEl, badgeEl) {
    badgeEl.innerText = "0 results";
    badgeEl.className = "badge badge-warning-count";
    resumeEl.innerHTML = `
        <div class="no-resume-state">
            <div class="icon-warning"><i class="fa-solid fa-file-circle-exclamation"></i></div>
            <p>Upload your resume in PDF/DOCX to match your skills dynamically.</p>
            <button id="btn-sidebar-upload" class="btn btn-primary btn-full">Upload Resume</button>
        </div>
    `;
    recsEl.innerHTML = `
        <div class="no-resume-state">
            <i class="fa-solid fa-cloud-arrow-up icon-warning"></i>
            <p>Your dashboard is empty. Upload a resume first to start receiving jobs matches.</p>
        </div>
    `;
    document.getElementById("btn-sidebar-upload").addEventListener("click", () => {
        window.location.hash = "#upload";
    });
}

// --- Job Detail Loading ---
async function loadJobDetails(jobId) {
    const detailsContainer = document.getElementById("view-job-details");
    
    // Reset view fields
    document.getElementById("details-job-title").innerText = "Loading...";
    document.getElementById("details-company").innerText = "";
    document.getElementById("details-location").innerText = "";
    document.getElementById("details-salary").innerText = "";
    document.getElementById("details-description").innerText = "";
    document.getElementById("container-matched-skills").innerHTML = "";
    document.getElementById("container-missing-skills").innerHTML = "";
    document.getElementById("details-match-score-badge").innerText = "0%";
    
    try {
        // Fetch recommendations to extract score/gaps for this specific job
        const recs = await apiRequest("/api/recommendations/");
        const rec = recs.find(r => r.job_id == jobId);
        
        if (!rec) {
            showToast("Could not find match detail for this job.", "error");
            window.location.hash = "#dashboard";
            return;
        }

        // Populating text fields
        document.getElementById("details-job-title").innerText = rec.job_title;
        document.getElementById("details-company").innerHTML = `<i class="fa-solid fa-building"></i> ${rec.company}`;
        document.getElementById("details-location").innerHTML = `<i class="fa-solid fa-location-dot"></i> ${rec.location}`;
        document.getElementById("details-salary").innerHTML = `<i class="fa-solid fa-money-bill-wave"></i> ${rec.salary || "Not Disclosed"}`;
        document.getElementById("details-description").innerText = rec.description;
        
        // Match score
        const scoreBadge = document.getElementById("details-match-score-badge");
        scoreBadge.innerText = `${rec.match_score}%`;
        
        // Color classification
        if (rec.match_score >= 80) {
            scoreBadge.style.color = "var(--color-success)";
            scoreBadge.style.borderColor = "var(--color-success)";
        } else {
            scoreBadge.style.color = "var(--color-secondary)";
            scoreBadge.style.borderColor = "var(--color-secondary)";
        }

        // Match lists
        const matched = rec.job_skills.filter(s => !rec.missing_skills.includes(s));
        
        document.getElementById("count-matched-skills").innerText = matched.length;
        document.getElementById("container-matched-skills").innerHTML = matched.length > 0
            ? matched.map(s => `<span class="tag">${s}</span>`).join("")
            : '<span class="color-text-muted" style="font-size:0.85rem">No matching skills detected.</span>';
            
        document.getElementById("count-missing-skills").innerText = rec.missing_skills.length;
        document.getElementById("container-missing-skills").innerHTML = rec.missing_skills.length > 0
            ? rec.missing_skills.map(s => `<span class="tag-missing">${s}</span>`).join("")
            : '<span class="badge badge-success" style="font-size:0.85rem"><i class="fa-solid fa-star"></i> Ready! No missing skills.</span>';
            
        // Update back CTA button links
        document.getElementById("btn-back-to-job").href = `#job/${jobId}`;
        
        // Wire Generate Roadmap button event
        const roadmapBtn = document.getElementById("btn-generate-roadmap");
        roadmapBtn.onclick = () => {
            window.location.hash = `#roadmap/${jobId}`;
        };
        
        if (rec.missing_skills.length === 0) {
            roadmapBtn.disabled = true;
            roadmapBtn.innerText = "No Skill Gaps to Fill!";
        } else {
            roadmapBtn.disabled = false;
            roadmapBtn.innerHTML = 'Generate Learning Roadmap <i class="fa-solid fa-route"></i>';
        }

    } catch (e) {
        showToast("Error loading job details.", "error");
        window.location.hash = "#dashboard";
    }
}

// --- Career Roadmap Generator ---
async function loadRoadmap(jobId) {
    const container = document.getElementById("roadmap-timeline-container");
    container.innerHTML = `
        <div class="loading-state">
            <i class="fa-solid fa-circle-notch fa-spin spinner"></i>
            <p>Analyzing skill paths and formatting projects...</p>
        </div>
    `;
    
    try {
        const roadmap = await apiRequest(`/api/recommendations/${jobId}/roadmap`);
        
        document.getElementById("roadmap-job-title").innerText = roadmap.job_title;
        document.getElementById("roadmap-subtitle").innerText = `Personalized preparation track for ${roadmap.company}`;
        
        if (!roadmap.learning_path || roadmap.learning_path.length === 0) {
            container.innerHTML = `
                <div class="glass-card" style="text-align:center; padding: 40px;">
                    <i class="fa-solid fa-circle-check" style="font-size:3rem; color:var(--color-success); margin-bottom:16px;"></i>
                    <h3>You are fully ready!</h3>
                    <p style="color:var(--color-text-muted); margin-top:8px">No gaps identified. You match all skill requirements for this post.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = roadmap.learning_path.map((step, idx) => {
            const topicList = step.topics.map(t => `<li>${t}</li>`).join("");
            const resourceList = step.resources.map(r => `<li>${r}</li>`).join("");
            
            return `
                <div class="glass-card roadmap-step-card">
                    <h3>
                        <span>Step ${idx + 1}: Master ${step.skill}</span>
                    </h3>
                    
                    <h4>Core Topics to Cover:</h4>
                    <ul>${topicList}</ul>
                    
                    <h4>Learning Resources:</h4>
                    <ul>${resourceList}</ul>
                    
                    <div class="project-box">
                        <strong>Project Task Milestone:</strong>
                        <p>${step.project}</p>
                    </div>
                </div>
            `;
        }).join("");

    } catch (e) {
        container.innerHTML = `
            <div class="glass-card" style="text-align:center; padding:40px;">
                <i class="fa-solid fa-circle-exclamation icon-warning"></i>
                <p>Failed to generate roadmap. Please check that your resume is uploaded.</p>
            </div>
        `;
    }
}

// --- Recruiter Dashboard loading ---
async function loadRecruiterData() {
    const jobsContainer = document.getElementById("recruiter-jobs-container");
    jobsContainer.innerHTML = '<p class="color-text-muted">Loading posted jobs...</p>';
    
    try {
        const jobs = await apiRequest("/api/jobs/");
        
        if (jobs && jobs.length > 0) {
            jobsContainer.innerHTML = jobs.map(job => `
                <div class="glass-card recruiter-job-card" id="rec-job-${job.id}">
                    <div>
                        <h3>${job.title}</h3>
                        <div class="company-meta">${job.location} | ${job.salary || "Not Specified"}</div>
                    </div>
                    <div class="job-actions">
                        <button class="btn btn-secondary btn-edit-job" data-id="${job.id}"><i class="fa-solid fa-pencil"></i></button>
                        <button class="btn btn-outline btn-delete-job" data-id="${job.id}"><i class="fa-solid fa-trash-can"></i></button>
                    </div>
                </div>
            `).join("");
            
            // Bind edit/delete handlers
            document.querySelectorAll(".btn-edit-job").forEach(btn => {
                btn.addEventListener("click", (e) => {
                    const jobId = btn.getAttribute("data-id");
                    editJobForm(jobId);
                });
            });

            document.querySelectorAll(".btn-delete-job").forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const jobId = btn.getAttribute("data-id");
                    if (confirm("Are you sure you want to delete this job posting?")) {
                        await deleteJobPosting(jobId);
                    }
                });
            });

        } else {
            jobsContainer.innerHTML = `
                <div class="no-resume-state">
                    <i class="fa-solid fa-folder-open icon-warning" style="font-size:2.5rem;"></i>
                    <p>No job postings created yet. Use the form on the left to add one.</p>
                </div>
            `;
        }
    } catch (e) {
        jobsContainer.innerHTML = '<p class="color-text-muted">Failed to load postings.</p>';
    }
}

// Edit active job
async function editJobForm(jobId) {
    try {
        const job = await apiRequest(`/api/jobs/${jobId}`);
        if (!job) return;
        
        document.getElementById("job-id-field").value = job.id;
        document.getElementById("job-title").value = job.title;
        document.getElementById("job-company").value = job.company;
        document.getElementById("job-location").value = job.location;
        document.getElementById("job-salary").value = job.salary || "";
        document.getElementById("job-description").value = job.description;
        
        document.getElementById("recruiter-form-title").innerText = "Edit Job Details";
        document.getElementById("btn-submit-job").innerText = "Save Changes";
        document.getElementById("btn-cancel-job").classList.remove("hidden");
    } catch (e) {
        showToast("Could not load job details for editing", "error");
    }
}

// Delete job posting
async function deleteJobPosting(jobId) {
    try {
        const success = await apiRequest(`/api/jobs/${jobId}`, { method: "DELETE" });
        if (success) {
            showToast("Job posting deleted.", "success");
            loadRecruiterData();
        }
    } catch (e) {
        showToast("Failed to delete posting.", "error");
    }
}

function resetJobForm() {
    document.getElementById("job-id-field").value = "";
    document.getElementById("form-job-post").reset();
    document.getElementById("recruiter-form-title").innerText = "Post New Job Opening";
    document.getElementById("btn-submit-job").innerText = "Post Opening";
    document.getElementById("btn-cancel-job").classList.add("hidden");
}

// ==========================================================================
// FILE UPLOAD ENGINE WITH DYNAMIC PROGRESS CALLBACKS
// ==========================================================================
let selectedFile = null;

function resetUploadForm() {
    selectedFile = null;
    document.getElementById("selected-file-name").classList.add("hidden");
    document.getElementById("selected-file-name").innerText = "";
    document.getElementById("btn-process-resume").disabled = true;
    document.getElementById("upload-progress-container").classList.add("hidden");
    document.getElementById("upload-progress-bar").style.width = "0%";
}

function handleFileSelection(file) {
    if (!file) return;
    
    // Validation
    const nameLower = file.name.toLowerCase();
    if (!nameLower.endsWith(".pdf") && !nameLower.endsWith(".docx")) {
        showToast("Unsupported file type. Please upload a PDF or DOCX file.", "error");
        resetUploadForm();
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showToast("File is too large. Max size is 5MB.", "error");
        resetUploadForm();
        return;
    }

    selectedFile = file;
    const nameEl = document.getElementById("selected-file-name");
    nameEl.innerText = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    nameEl.classList.remove("hidden");
    document.getElementById("btn-process-resume").disabled = false;
}

// AJAX form submit with progress monitor
function uploadResumeFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    const progressContainer = document.getElementById("upload-progress-container");
    const progressBar = document.getElementById("upload-progress-bar");
    const progressText = document.getElementById("upload-status-text");
    const uploadBtn = document.getElementById("btn-process-resume");

    progressContainer.classList.remove("hidden");
    uploadBtn.disabled = true;

    // Use XMLHttpRequest for real-time progress callbacks
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/resumes/upload`);
    
    // Inject Authorization header
    if (state.token) {
        xhr.setRequestHeader("Authorization", `Bearer ${state.token}`);
    }

    // Monitor upload progress
    xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressBar.style.width = `${percent}%`;
            progressText.innerText = `Uploading resume... ${percent}%`;
            if (percent === 100) {
                progressText.innerText = "Parsing text and calculating semantic vectors. Please wait...";
            }
        }
    });

    // Monitor complete response
    xhr.onload = () => {
        if (xhr.status === 200 || xhr.status === 201) {
            showToast("Resume parsed and matches calculated!", "success");
            setTimeout(() => {
                window.location.hash = "#dashboard";
            }, 1000);
        } else {
            let errorMsg = "Upload failed";
            try {
                const res = JSON.parse(xhr.responseText);
                errorMsg = res.detail || errorMsg;
            } catch (err) {}
            showToast(errorMsg, "error");
            progressText.innerText = "Upload failed.";
            progressBar.style.backgroundColor = "var(--color-danger)";
            uploadBtn.disabled = false;
        }
    };

    xhr.onerror = () => {
        showToast("Network connection error.", "error");
        progressText.innerText = "Upload error.";
        progressBar.style.backgroundColor = "var(--color-danger)";
        uploadBtn.disabled = false;
    };

    xhr.send(formData);
}

// ==========================================================================
// EVENT LISTENERS & DOM HOOKS
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Initial State UI checks
    updateNavUI();
    router();
    
    // 2. Hash and Navigation listeners
    window.addEventListener("hashchange", router);
    
    document.getElementById("btn-login-nav").addEventListener("click", () => {
        window.location.hash = "#login";
    });
    
    document.getElementById("btn-logout-nav").addEventListener("click", handleLogout);
    
    document.getElementById("btn-get-started").addEventListener("click", () => {
        if (state.token) {
            window.location.hash = (state.role === "recruiter") ? "#recruiter" : "#dashboard";
        } else {
            window.location.hash = "#register";
        }
    });
    
    document.getElementById("btn-view-demo-jobs").addEventListener("click", () => {
        if (state.token) {
            window.location.hash = (state.role === "recruiter") ? "#recruiter" : "#dashboard";
        } else {
            window.location.hash = "#login";
            showToast("Log in to explore our active jobs bank", "info");
        }
    });

    // 3. Form Submit Listeners
    // --- Login Form ---
    document.getElementById("form-login").addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        
        try {
            const data = await apiRequest("/api/auth/login", {
                method: "POST",
                body: { email, password }
            });
            if (data) {
                // Fetch profile to get role using apiRequest for robust error handling
                const profile = await apiRequest("/api/auth/me", {
                    headers: { "Authorization": `Bearer ${data.access_token}` }
                });
                
                if (profile) {
                    handleLoginSuccess(data.access_token, profile.role);
                }
            }
        } catch (err) {}
    });

    // --- Register Form ---
    document.getElementById("form-register").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("register-name").value;
        const email = document.getElementById("register-email").value;
        const role = document.getElementById("register-role").value;
        const password = document.getElementById("register-password").value;
        
        if (password.length < 6) {
            showToast("Password must be at least 6 characters.", "error");
            return;
        }

        try {
            const data = await apiRequest("/api/auth/register", {
                method: "POST",
                body: { name, email, role, password }
            });
            if (data) {
                showToast("Account created successfully! Please sign in.", "success");
                document.getElementById("login-email").value = email;
                toggleAuthForms(false);
                window.location.hash = "#login";
            }
        } catch (err) {}
    });

    // Toggle links in auth card
    document.getElementById("link-to-register").addEventListener("click", (e) => {
        e.preventDefault();
        window.location.hash = "#register";
    });
    
    document.getElementById("link-to-login").addEventListener("click", (e) => {
        e.preventDefault();
        window.location.hash = "#login";
    });

    // --- Recruiter Job Creation ---
    document.getElementById("form-job-post").addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("job-id-field").value;
        const title = document.getElementById("job-title").value;
        const company = document.getElementById("job-company").value;
        const location = document.getElementById("job-location").value;
        const salary = document.getElementById("job-salary").value;
        const description = document.getElementById("job-description").value;
        
        const jobData = { title, company, location, salary, description };
        
        try {
            let data;
            if (id) {
                // Update
                data = await apiRequest(`/api/jobs/${id}`, {
                    method: "PUT",
                    body: jobData
                });
                showToast("Job posting updated successfully!", "success");
            } else {
                // Create
                data = await apiRequest("/api/jobs/", {
                    method: "POST",
                    body: jobData
                });
                showToast("Job vacancy posted successfully!", "success");
            }
            if (data) {
                resetJobForm();
                loadRecruiterData();
            }
        } catch (err) {}
    });

    document.getElementById("btn-cancel-job").addEventListener("click", resetJobForm);

    // --- Drag and Drop File Input Listeners ---
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("resume-file-input");

    dropZone.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Drag-over styling hooks
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
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    // Process Resume button click
    document.getElementById("btn-process-resume").addEventListener("click", () => {
        if (selectedFile) {
            uploadResumeFile(selectedFile);
        }
    });
});
