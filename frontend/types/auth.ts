export type User = {
  id: string;
  nama: string;
  nik: string;
  user_level: string;
  fungsi: string | null;
  is_active: boolean;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};
