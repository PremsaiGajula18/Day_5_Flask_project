/* ── script.js ──────────────────────────────────────────
   Handles registration form validation and submission
   via FormData and fetch() API to Flask backend.
   Supports uploading real physical photos to static/uploads.
   ────────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("registrationForm");
    const messageBox = document.getElementById("message");
    const submitBtn = document.getElementById("submitBtn");

    if (!form) return;

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        // 1. Clear previous errors & messages
        document.querySelectorAll(".field-error").forEach(el => el.textContent = "");
        messageBox.style.display = "none";
        messageBox.className = "message-banner";

        // 2. Read values
        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const dob = document.getElementById("dob").value;

        const genderInput = document.querySelector('input[name="gender"]:checked');
        const gender = genderInput ? genderInput.value : "";

        const course = document.getElementById("course").value;
        const qualification = document.getElementById("qualification").value;

        const trainingModeInput = document.querySelector('input[name="training_mode"]:checked');
        const trainingMode = trainingModeInput ? trainingModeInput.value : "";

        // Collect all checked skills
        const checkedSkills = Array.from(document.querySelectorAll('input[name="skills"]:checked'))
            .map(cb => cb.value);

        const experience = document.getElementById("experience").value;
        const address = document.getElementById("address").value.trim();
        const website = document.getElementById("website").value.trim();

        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm_password").value;
        const agree = document.getElementById("agree").checked;

        // Photo file input
        const photoInput = document.getElementById("photo");

        // 3. Client-side Validation
        let hasError = false;

        function setError(fieldId, errorMsg) {
            const errEl = document.getElementById(fieldId);
            if (errEl) errEl.textContent = errorMsg;
            hasError = true;
        }

        if (!name) setError("err-name", "Please enter your full name.");
        if (!email) setError("err-email", "Please enter your email address.");
        if (!phone) setError("err-phone", "Please enter your mobile number.");
        if (!dob) setError("err-dob", "Please select your date of birth.");
        if (!gender) setError("err-gender", "Please select a gender.");
        if (!course) setError("err-course", "Please choose a course.");
        if (!qualification) setError("err-qualification", "Please choose your qualification.");
        if (!trainingMode) setError("err-training_mode", "Please select a training mode.");
        if (checkedSkills.length === 0) setError("err-skills", "Please select at least one skill.");
        if (experience === "") setError("err-experience", "Please enter years of experience.");
        if (!address) setError("err-address", "Please enter your address.");
        if (!password) setError("err-password", "Please enter a password.");
        if (!confirmPassword) setError("err-confirm_password", "Please confirm your password.");

        if (password && confirmPassword && password !== confirmPassword) {
            setError("err-confirm_password", "Passwords do not match.");
        }

        if (!agree) {
            setError("err-agree", "You must agree to register.");
        }

        // Validate photo file size (under 2 MB)
        if (photoInput.files && photoInput.files.length > 0) {
            const file = photoInput.files[0];
            if (file.size > 2 * 1024 * 1024) {
                setError("err-photo", "Photo must be under 2 MB.");
            }
        }

        if (hasError) {
            messageBox.textContent = "Please fix the errors highlighted below.";
            messageBox.className = "message-banner error";
            messageBox.style.display = "block";
            messageBox.scrollIntoView({ behavior: "smooth", block: "center" });
            return;
        }

        // 4. Build FormData Payload (to support binary image upload)
        const formData = new FormData();
        formData.append("name", name);
        formData.append("email", email);
        formData.append("phone", phone);
        formData.append("dob", dob);
        formData.append("gender", gender);
        formData.append("course", course);
        formData.append("qualification", qualification);
        formData.append("training_mode", trainingMode);
        formData.append("skills", checkedSkills.join(", "));
        formData.append("experience", parseInt(experience, 10) || 0);
        formData.append("address", address);
        formData.append("website", website);
        formData.append("password", password);
        formData.append("confirm_password", confirmPassword);
        formData.append("agree", agree ? "true" : "false");

        // Append actual physical photo file if selected
        if (photoInput.files && photoInput.files.length > 0) {
            formData.append("photo", photoInput.files[0]);
        }

        // 5. Submit via fetch()
        submitBtn.disabled = true;
        submitBtn.textContent = "Registering...";

        fetch("/api/register", {
            method: "POST",
            // Do NOT set Content-Type header; browser automatically sets multipart/form-data boundary
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(result => {
            submitBtn.disabled = false;
            submitBtn.textContent = "Create registration";

            if (result.status === 200 || result.body.status === "success") {
                messageBox.textContent = "✅ " + (result.body.message || "Registration successful!");
                messageBox.className = "message-banner success";
                messageBox.style.display = "block";

                form.reset();
                document.getElementById("experience").value = "0";

                messageBox.scrollIntoView({ behavior: "smooth", block: "center" });
            } else {
                messageBox.textContent = "❌ " + (result.body.message || "Registration failed.");
                messageBox.className = "message-banner error";
                messageBox.style.display = "block";
                messageBox.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        })
        .catch(err => {
            submitBtn.disabled = false;
            submitBtn.textContent = "Create registration";

            console.error("Submission error:", err);
            messageBox.textContent = "❌ Network error. Please check your connection and try again.";
            messageBox.className = "message-banner error";
            messageBox.style.display = "block";
        });
    });
});
