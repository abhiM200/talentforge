/**
 * TalentForge — Sample Job Descriptions
 * Helper to pre-fill job description textarea for demos
 */

const SAMPLE_JOB_DESCRIPTIONS = {
    "software_engineer": `Senior Software Engineer — Python & Cloud

We are looking for a Senior Software Engineer to join our growing engineering team. You will design, build, and maintain scalable backend services and APIs.

Requirements:
• 3+ years of professional software engineering experience
• Strong proficiency in Python and REST API development
• Experience with cloud platforms (AWS or GCP preferred)
• Familiarity with Docker, Kubernetes, and CI/CD pipelines
• Proficient in SQL and NoSQL databases (PostgreSQL, MongoDB, Redis)
• Understanding of microservices architecture
• Experience with Git and code review processes
• Strong problem-solving and communication skills

Nice to have:
• Experience with machine learning or data pipelines
• Contributions to open-source projects
• Agile / Scrum experience`,

    "data_scientist": `Data Scientist — Machine Learning & Analytics

We are seeking a Data Scientist to develop predictive models and drive data-informed decision making across the organization.

Requirements:
• 2+ years of experience in data science or machine learning
• Proficiency in Python (pandas, numpy, scikit-learn, matplotlib)
• Experience with machine learning algorithms (classification, regression, clustering)
• Strong SQL skills for data extraction and analysis
• Experience with data visualization tools (Tableau, Power BI, or matplotlib/seaborn)
• Solid foundation in statistics and probability
• Ability to communicate insights to non-technical stakeholders

Nice to have:
• Experience with deep learning frameworks (TensorFlow or PyTorch)
• Familiarity with Spark or big data tools
• Experience with A/B testing and experimentation`,

    "fullstack": `Full Stack Developer — React & Node.js

We're building the next generation of our SaaS platform and need a full-stack developer who can own features end-to-end.

Requirements:
• 3+ years of full-stack development experience
• Strong proficiency in React and TypeScript
• Solid backend skills in Node.js and Express
• Experience designing and consuming REST APIs and GraphQL
• Proficiency in HTML, CSS, and responsive design
• Database experience with PostgreSQL and MongoDB
• Version control with Git and collaborative workflows
• Experience deploying to cloud environments (AWS, Vercel, or similar)

Nice to have:
• Experience with Next.js or similar SSR frameworks
• Docker and containerization knowledge
• Testing experience (Jest, Cypress)`,

    "devops": `DevOps / Cloud Infrastructure Engineer

Join our platform team to build and maintain world-class infrastructure that powers millions of users.

Requirements:
• 3+ years in DevOps, SRE, or cloud infrastructure roles
• Deep expertise in AWS (EC2, S3, RDS, Lambda, ECS/EKS)
• Proficiency with Infrastructure as Code (Terraform or CloudFormation)
• Strong experience with Docker and Kubernetes
• CI/CD pipeline design and maintenance (GitHub Actions, Jenkins, or GitLab CI)
• Linux administration and shell scripting
• Monitoring and alerting (CloudWatch, Datadog, Prometheus/Grafana)
• Strong security mindset and experience with IAM and VPCs

Nice to have:
• Azure or GCP experience
• Experience with Ansible or configuration management
• On-call rotation experience`
};

/**
 * Fill the job description textarea with a sample
 * @param {string} key - One of: software_engineer, data_scientist, fullstack, devops
 */
function fillSampleJD(key) {
    const jdTextarea = document.getElementById('job-description');
    if (jdTextarea && SAMPLE_JOB_DESCRIPTIONS[key]) {
        jdTextarea.value = SAMPLE_JOB_DESCRIPTIONS[key];
        jdTextarea.focus();

        // Visual feedback
        jdTextarea.style.borderColor = '#3b82f6';
        setTimeout(() => {
            jdTextarea.style.borderColor = '';
        }, 1000);
    }
}

// Expose globally
window.fillSampleJD = fillSampleJD;
window.SAMPLE_JOB_DESCRIPTIONS = SAMPLE_JOB_DESCRIPTIONS;
