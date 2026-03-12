(function () {
    var root = document.documentElement;
    var body = document.body;
    var content = document.getElementById("driver-content");
    var installPromptEvent = null;
    var currentTab = body.dataset.initialTab || "dashboard";
    var isSpa = body.dataset.driverSpa === "1";
    var assignmentStateUrl = body.dataset.assignmentStateUrl || "";
    var previousAssignmentState = null;
    var toastTimer = null;

    var partialUrls = {
        dashboard: body.dataset.urlDashboard || "",
        trips: body.dataset.urlTrips || "",
        fuel: body.dataset.urlFuel || "",
        profile: body.dataset.urlProfile || "",
    };

    function updateThemeIcon() {
        var icon = document.getElementById("theme-toggle-icon");
        if (!icon) return;
        icon.textContent = root.classList.contains("dark") ? "light_mode" : "dark_mode";
    }

    function setActiveDriverTab(tabName) {
        var tabs = document.querySelectorAll(".driver-tab");
        tabs.forEach(function (tab) {
            var isActive = tab.dataset.tab === tabName;
            tab.classList.toggle("text-sky-700", isActive);
            tab.classList.toggle("text-slate-400", !isActive);
            tab.classList.toggle("dark:text-sky-400", isActive);
            tab.classList.toggle("dark:text-slate-500", !isActive);
        });
    }

    function toggleTheme() {
        var isDark = root.classList.toggle("dark");
        localStorage.setItem("driver-theme", isDark ? "dark" : "light");
        updateThemeIcon();
    }

    function showToast(message, href) {
        var toast = document.getElementById("driver-toast");
        if (!toast) return;
        if (toastTimer) clearTimeout(toastTimer);
        toast.classList.remove("hidden");
        toast.innerHTML = "";

        var row = document.createElement("div");
        row.className = "flex items-center justify-between gap-3";

        var label = document.createElement("span");
        label.textContent = message;
        row.appendChild(label);

        if (href) {
            var link = document.createElement("a");
            link.href = href;
            link.className = "shrink-0 font-semibold underline";
            link.textContent = "Open";
            row.appendChild(link);
        }

        toast.appendChild(row);
        toastTimer = setTimeout(function () {
            toast.classList.add("hidden");
        }, 5000);
    }

    function refreshDriverContent() {
        if (!isSpa || !content || document.hidden) return;
        var url = partialUrls[currentTab];
        if (!url) return;

        if (window.htmx && typeof window.htmx.ajax === "function") {
            window.htmx.ajax("GET", url, { target: "#driver-content", swap: "innerHTML" });
            return;
        }

        fetch(url, { credentials: "same-origin" })
            .then(function (r) {
                if (!r.ok) throw new Error("refresh failed");
                return r.text();
            })
            .then(function (html) {
                content.innerHTML = html;
            })
            .catch(function () {});
    }

    function setupPwaInstall() {
        var installBtn = document.getElementById("install-app");
        if (!installBtn) return;

        window.addEventListener("beforeinstallprompt", function (event) {
            event.preventDefault();
            installPromptEvent = event;
            installBtn.classList.remove("hidden");
        });

        installBtn.addEventListener("click", function () {
            if (!installPromptEvent) {
                alert("For iPhone: Share > Add to Home Screen");
                return;
            }
            installPromptEvent.prompt();
            installPromptEvent.userChoice.finally(function () {
                installPromptEvent = null;
                installBtn.classList.add("hidden");
            });
        });
    }

    function setupServiceWorker() {
        var swUrl = body.dataset.swUrl;
        if (!swUrl || !("serviceWorker" in navigator)) return;
        navigator.serviceWorker.register(swUrl).catch(function () {});
    }

    function checkAssignedTripUpdates() {
        if (!assignmentStateUrl || document.hidden) return;
        fetch(assignmentStateUrl, { credentials: "same-origin" })
            .then(function (r) {
                if (!r.ok) throw new Error("assignment state failed");
                return r.json();
            })
            .then(function (state) {
                if (!previousAssignmentState) {
                    previousAssignmentState = state;
                    return;
                }

                var hasNewAssignment = (
                    Number(state.assigned_count || 0) > Number(previousAssignmentState.assigned_count || 0) ||
                    (state.latest_assigned_trip_id && state.latest_assigned_trip_id !== previousAssignmentState.latest_assigned_trip_id)
                );

                if (hasNewAssignment) {
                    var order = state.latest_assigned_order || "New trip assigned";
                    showToast("New trip assigned: " + order, "/transport/driver/trips/");
                    refreshDriverContent();
                }
                previousAssignmentState = state;
            })
            .catch(function () {});
    }

    document.addEventListener("click", function (event) {
        var themeBtn = event.target.closest("#theme-toggle");
        if (themeBtn) {
            toggleTheme();
            return;
        }

        var tab = event.target.closest(".driver-tab");
        if (tab) {
            currentTab = tab.dataset.tab || "dashboard";
            setActiveDriverTab(currentTab);
        }
    });

    document.body.addEventListener("htmx:afterSwap", function (event) {
        if (!event.target || event.target.id !== "driver-content") return;
        var section = event.target.firstElementChild && event.target.firstElementChild.dataset
            ? event.target.firstElementChild.dataset.section
            : null;
        if (section) {
            currentTab = section;
            setActiveDriverTab(section);
        }
    });

    updateThemeIcon();
    setActiveDriverTab(currentTab);
    setupPwaInstall();
    setupServiceWorker();
    checkAssignedTripUpdates();
    if (isSpa) {
        setInterval(refreshDriverContent, 20000);
        setInterval(checkAssignedTripUpdates, 15000);
    }
})();
