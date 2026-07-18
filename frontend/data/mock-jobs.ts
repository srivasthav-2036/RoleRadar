export interface MockJob {
  id: string;
  title: string;
  company: string;
  location: string;
  score: number;
  matchedSkills: string[];
  missingSkills: string[];
  postedAt: string;
  type: string;
}

export const mockJobs: MockJob[] = [
  {
    id: "1",
    title: "Machine Learning Engineer",
    company: "Anthropic",
    location: "Remote",
    score: 94,
    matchedSkills: ["Python", "PyTorch", "FastAPI", "Vector Search"],
    missingSkills: ["Kubernetes"],
    postedAt: "2h ago",
    type: "Full-time",
  },
  {
    id: "2",
    title: "Backend Engineer, Platform",
    company: "Vercel",
    location: "Remote \u00b7 US",
    score: 89,
    matchedSkills: ["TypeScript", "Node.js", "PostgreSQL"],
    missingSkills: ["Go", "gRPC"],
    postedAt: "5h ago",
    type: "Full-time",
  },
  {
    id: "3",
    title: "AI/ML Intern",
    company: "Stripe",
    location: "Bengaluru, IN",
    score: 82,
    matchedSkills: ["Python", "scikit-learn", "SQL"],
    missingSkills: ["Spark"],
    postedAt: "1d ago",
    type: "Internship",
  },
  {
    id: "4",
    title: "Data Engineer",
    company: "Linear",
    location: "Remote",
    score: 76,
    matchedSkills: ["Python", "Airflow"],
    missingSkills: ["dbt", "Snowflake"],
    postedAt: "1d ago",
    type: "Full-time",
  },
];

export const mockStats = {
  totalMatches: 47,
  avgScore: 81,
  tailoredResumes: 12,
  newThisWeek: 9,
};

export const mockSkillCoverage = [
  { skill: "Python", coverage: 96 },
  { skill: "SQL", coverage: 88 },
  { skill: "Machine Learning", coverage: 74 },
  { skill: "Cloud / AWS", coverage: 41 },
  { skill: "System Design", coverage: 35 },
];
