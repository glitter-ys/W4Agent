export interface Project {
  id: string;
  name: string;
  description: string | null;
  base_url: string;
  owner: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  base_url: string;
}
