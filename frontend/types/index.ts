export interface SessionUser {
  google_id: string;
  email: string;
  first_name: string;
  is_demo?: boolean;
}

export interface RepoSummary {
  repo_url: string;
  page_name: string;
  can_update_wiki: boolean;
}

export interface DocResponse {
  repo_url: string;
  page_name: string;
  content: string;
  updated_at: string | null;
}
