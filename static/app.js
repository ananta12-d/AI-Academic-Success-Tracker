const { createApp, ref, computed, watch, onMounted } = Vue;

createApp({
    setup() {
        // --- STATE VARIABLES ---
        const liveDrivers = ref([]);
        const isDarkMode = ref(false);
        const currentTab = ref('classroom');
        const selectedCourse = ref('BCA');
        const students = ref([]);
        const courseStats = ref(null);

        const simData = ref(null);
        const livePrediction = ref(null);
        let chartInstance = null;
        let classChartInstance = null;
        let interactiveChartInstance = null;
        let pdfChartInstance = null;
        const isModalOpen = ref(false);

        // --- COMPUTED PROPERTIES ---
        const safeStudents = computed(() => students.value.filter(s => s.predicted_risk === 0).sort((a, b) => b.previous_cgpa - a.previous_cgpa));
        const atRiskStudents = computed(() => students.value.filter(s => s.predicted_risk === 1).sort((a, b) => a.attendance - b.attendance));
        const passRate = computed(() => students.value.length === 0 ? 0 : ((safeStudents.value.length / students.value.length) * 100).toFixed(1));

        const dynamicSuggestions = computed(() => {
            const rules = [];
            if (!courseStats.value || students.value.length === 0) return rules;
            const rate = parseFloat(passRate.value);
            if (rate < 60) rules.push(`🚨 CRITICAL: The projected pass rate is only ${rate}%. Immediate academic intervention required.`);
            else if (rate >= 85) rules.push(`🌟 EXCELLENT: High pass rate of ${rate}%. Focus on advanced career placement prep.`);
            if (courseStats.value.avg_attendance < 65) rules.push(`⚠️ ATTENDANCE ALERT: Class average is dangerously low. Trigger automated SMS to parents.`);
            const struggling = students.value.filter(s => s.assignments_completed < 5).length;
            if (struggling > (students.value.length * 0.3)) rules.push(`📝 WORKLOAD ISSUE: ${struggling} students failing to submit assignments. Revise pacing.`);
            if (rules.length === 0) rules.push(`✅ ON TRACK: Class metrics are stable. Maintain current methodologies.`);
            return rules;
        });

        const studentSuggestions = computed(() => {
            const rules = [];
            if (!simData.value) return rules;
            const data = simData.value;
            const totalMarks = data.internal_marks + data.unit_test_marks;
            if (data.attendance < 75) rules.push(`⚠️ Attendance (${data.attendance}%) is low. Target 80%.`);
            if (totalMarks < 35) rules.push(`📚 Exam scores are critical. Focus on foundational concepts.`);
            if (data.assignments_completed < 7) rules.push(`📝 Missed ${10 - data.assignments_completed} assignments. Submitting coursework helps.`);
            if (data.study_hours_weekly < 10 && totalMarks < 45) rules.push(`⏱️ Study time is too low relative to scores. Double this.`);
            if (rules.length === 0) rules.push(`🌟 Outstanding performance! Strong pathway to high honors.`);
            return rules;
        });

        // --- AUTH & THEME ---
        const logout = () => {
            localStorage.removeItem('token');
            window.location.href = '/login';
        };

        const toggleTheme = () => {
            isDarkMode.value = !isDarkMode.value;
            document.documentElement.setAttribute('data-theme', isDarkMode.value ? 'dark' : 'light');
            if (chartInstance && simData.value) drawChart();
        };

        // --- DATA LOADING & PREDICTION ---
        const loadCourseData = async () => {
            let token = localStorage.getItem('token');
            if (!token || token === 'undefined' || token === 'null') return logout();
            token = token.replace(/['"]+/g, '').trim();

            const headers = { 'Authorization': `Bearer ${token}` };

            try {
                const studentRes = await fetch(`/api/students/${selectedCourse.value}`, { headers });
                if (studentRes.status === 401 || studentRes.status === 422) return logout();
                if (studentRes.ok) students.value = await studentRes.json();

                const statsRes = await fetch(`/api/course_stats/${selectedCourse.value}`, { headers });
                if (statsRes.ok) courseStats.value = await statsRes.json();

                simData.value = null;
                setTimeout(() => drawClassChart(), 100);
            } catch (error) { console.error("API Error in loadCourseData:", error); }
        };

        const fetchLivePrediction = async () => {
            if (!simData.value) return;
            let token = localStorage.getItem('token');
            if (!token || token === 'undefined' || token === 'null') return logout();
            token = token.replace(/['"]+/g, '').trim();

            try {
                const res = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify(simData.value)
                });
                if (res.status === 401 || res.status === 422) return logout();

                const data = await res.json();
                livePrediction.value = data.at_risk;
                liveDrivers.value = data.ai_drivers;
                drawChart();
            } catch (error) { console.error("Predict Error:", error); }
        };

        const selectStudent = (student) => {
            simData.value = JSON.parse(JSON.stringify(student));
            livePrediction.value = student.predicted_risk;
            setTimeout(() => drawChart(), 50);
        };

        const openModal = () => { isModalOpen.value = true; setTimeout(() => drawInteractiveChart(), 100); };
        const closeModal = () => { isModalOpen.value = false; };

        // --- CHART DRAWING FUNCTIONS ---
        const drawClassChart = () => {
            const canvas = document.getElementById('classBarChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const textColor = isDarkMode.value ? '#f8fafc' : '#1e293b';

            if (classChartInstance) classChartInstance.destroy();
            classChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Safe (On Track)', 'At Risk (Needs Attention)'],
                    datasets: [{ label: 'Students', data: [safeStudents.value.length, atRiskStudents.value.length], backgroundColor: ['#10b981', '#ef4444'], borderRadius: 6 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { color: textColor } }, x: { ticks: { color: textColor } } } }
            });
        };

        const drawChart = () => {
            const canvas = document.getElementById('liveRadarChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const currentData = [ simData.value.attendance, (simData.value.internal_marks / 30) * 100, (simData.value.unit_test_marks / 50) * 100, (simData.value.assignments_completed / 10) * 100 ];
            const avgData = [ courseStats.value.avg_attendance, (courseStats.value.avg_internal / 30) * 100, (courseStats.value.avg_unit / 50) * 100, 80 ];
            const textColor = isDarkMode.value ? '#f8fafc' : '#1e293b';
            const gridColor = isDarkMode.value ? '#334155' : '#e2e8f0';

            if (chartInstance) {
                chartInstance.data.datasets[0].data = currentData;
                chartInstance.options.scales.r.pointLabels.color = textColor;
                chartInstance.options.scales.r.grid.color = gridColor;
                chartInstance.options.scales.r.angleLines.color = gridColor;
                if (chartInstance.options.plugins && chartInstance.options.plugins.legend) chartInstance.options.plugins.legend.labels.color = textColor;
                chartInstance.update(); return;
            }

            chartInstance = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['Attendance', 'Internal Marks', 'Unit Test', 'Assignments'],
                    datasets: [ { label: 'Student', data: currentData, backgroundColor: 'rgba(59, 130, 246, 0.4)', borderColor: '#3b82f6', borderWidth: 2 }, { label: 'Class Average', data: avgData, backgroundColor: 'rgba(148, 163, 184, 0.2)', borderColor: '#94a3b8', borderWidth: 2 } ]
                },
                options: { layout: { padding: 25 }, responsive: true, scales: { r: { min: 0, max: 100, pointLabels: { color: textColor, font: { size: 13 } }, grid: { color: gridColor }, angleLines: { color: gridColor }, ticks: { display: false } } }, plugins: { legend: { labels: { color: textColor } } } }
            });
        };

        const drawInteractiveChart = () => {
            const canvas = document.getElementById('interactiveRadarChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const currentData = [ simData.value.attendance, (simData.value.internal_marks / 30) * 100, (simData.value.unit_test_marks / 50) * 100, (simData.value.assignments_completed / 10) * 100 ];
            const avgData = [ courseStats.value.avg_attendance, (courseStats.value.avg_internal / 30) * 100, (courseStats.value.avg_unit / 50) * 100, 80 ];
            const textColor = isDarkMode.value ? '#f8fafc' : '#1e293b';
            const gridColor = isDarkMode.value ? '#334155' : '#e2e8f0';

            if (interactiveChartInstance) interactiveChartInstance.destroy();
            interactiveChartInstance = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['Attendance', 'Internal Marks', 'Unit Test', 'Assignments'],
                    datasets: [ { label: 'Student', data: currentData, backgroundColor: 'rgba(59, 130, 246, 0.4)', borderColor: '#3b82f6', borderWidth: 3, pointRadius: 8, pointHoverRadius: 10 }, { label: 'Class Average', data: avgData, backgroundColor: 'rgba(148, 163, 184, 0.2)', borderColor: '#94a3b8', borderWidth: 2 } ]
                },
                options: { 
                    responsive: true, maintainAspectRatio: false, scales: { r: { min: 0, max: 100, pointLabels: { color: textColor, font: { size: 14, weight: 'bold' } }, grid: { color: gridColor }, angleLines: { color: gridColor } } },
                    plugins: { 
                        legend: { labels: { color: textColor } },
                        dragData: {
                            round: 1, showTooltip: true,
                            onDragEnd: function(e, datasetIndex, index, value) {
                                if (datasetIndex === 0) {
                                    if (index === 0) simData.value.attendance = Math.round(value);
                                    if (index === 1) simData.value.internal_marks = Math.round((value / 100) * 30);
                                    if (index === 2) simData.value.unit_test_marks = Math.round((value / 100) * 50);
                                    if (index === 3) simData.value.assignments_completed = Math.round((value / 100) * 10);
                                }
                            }
                        }
                    }
                }
            });
        };

        // --- WATCHERS ---
        watch(simData, (newVal) => { if (newVal) fetchLivePrediction(); }, { deep: true });
        watch(currentTab, (newTab) => { if (newTab === 'individual' && simData.value) setTimeout(() => drawChart(), 50); });

        // --- REPORT GENERATION (PDF / CSV) ---
        const downloadClassCSV = () => {
            if (students.value.length === 0) return;
            let csvContent = "data:text/csv;charset=utf-8,Student Name,Roll Number,Attendance (%),Total Marks (/80),Assignments Completed,AI Predicted Status\n";
            students.value.forEach(s => {
                const totalMarks = s.internal_marks + s.unit_test_marks;
                const status = s.predicted_risk === 1 ? "At Risk" : "Safe";
                csvContent += `"${s.student_name}",${s.roll_no},${s.attendance},${totalMarks},${s.assignments_completed},${status}\n`;
            });
            const link = document.createElement("a");
            link.setAttribute("href", encodeURI(csvContent));
            link.setAttribute("download", `Class_Report_${selectedCourse.value}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        };

        const downloadClassPDF = async () => {
            const element = document.getElementById('formal-analytical-report');
            const summaryElement = document.getElementById('ai-class-remarks');
            const mentorElement = document.getElementById('ai-mentor-verdict');
            
            summaryElement.innerText = "Generating AI Analysis...";
            mentorElement.innerText = "Consulting AI Mentor Core...";

            try {
                let token = localStorage.getItem('token').replace(/['"]+/g, '').trim();
                const aiRes = await fetch('/api/generate_admin_report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({
                        type: 'class',
                        course: selectedCourse.value,
                        pass_rate: passRate.value,
                        at_risk_count: atRiskStudents.value.length,
                        total_students: students.value.length
                    })
                });

                if (aiRes.ok) {
                    const data = await aiRes.json();
                    // Split the summary and mentor verdict using our delimiter
                    const parts = data.report.split('|||');
                    summaryElement.innerText = parts[0]?.trim() || "Summary unavailable.";
                    mentorElement.innerText = parts[1]?.trim() || "Mentor points unavailable.";
                }
            } catch (e) { 
                summaryElement.innerText = "AI Generation Failed."; 
                mentorElement.innerText = "Manual intervention required.";
            }

            const ctx = document.getElementById('pdfPieChart');
            if (ctx) {
                if (pdfChartInstance) pdfChartInstance.destroy();
                pdfChartInstance = new Chart(ctx.getContext('2d'), {
                    type: 'doughnut',
                    data: { labels: ['On Track', 'Support Needed'], datasets: [{ data: [safeStudents.value.length, atRiskStudents.value.length], backgroundColor: ['#10b981', '#ef4444'], borderWidth: 0 }] },
                    options: { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { position: 'bottom', labels: { color: '#1e293b', font: { size: 14 } } } } }
                });
            }

            element.style.left = '0';
            element.style.position = 'relative';
            const opt = { margin: 0.2, filename: `Cohort_Analysis_${selectedCourse.value}.pdf`, image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' } };
            html2pdf().set(opt).from(element).save().then(() => { element.style.left = '-9999px'; element.style.position = 'absolute'; });
        };

        const downloadStudentPDF = async () => {
            if (!simData.value) return;
            const element = document.getElementById('formal-student-report');
            const remarkElement = document.getElementById('ai-student-remarks');
            document.getElementById('pdf-date').innerText = new Date().toLocaleDateString();
            
            remarkElement.innerText = "Generating personalized remarks...";
            try {
                let token = localStorage.getItem('token').replace(/['"]+/g, '').trim();
                const aiRes = await fetch('/api/generate_admin_report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                    body: JSON.stringify({ type: 'student', name: simData.value.student_name, attendance: simData.value.attendance, marks: simData.value.internal_marks + simData.value.unit_test_marks, assignments: simData.value.assignments_completed })
                });
                if (aiRes.ok) {
                    const data = await aiRes.json();
                    remarkElement.innerText = data.report;
                }
            } catch (e) { remarkElement.innerText = "AI Generation Failed."; }

            element.style.left = '0';
            element.style.position = 'relative';
            const opt = { margin: 0.2, filename: `Student_Analysis_${simData.value.roll_no}.pdf`, image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' } };
            html2pdf().set(opt).from(element).save().then(() => { element.style.left = '-9999px'; element.style.position = 'absolute'; });
        };

        onMounted(() => { loadCourseData(); });

        return { 
            isDarkMode, toggleTheme, currentTab, selectedCourse, students, courseStats, simData, livePrediction, loadCourseData, selectStudent,
            safeStudents, atRiskStudents, passRate, dynamicSuggestions, isModalOpen, openModal, closeModal, studentSuggestions,
            downloadClassCSV, downloadStudentPDF, downloadClassPDF, logout, liveDrivers, fetchLivePrediction
        };
    }
}).mount('#app');