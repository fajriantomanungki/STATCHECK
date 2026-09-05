export type User = {
  id: string;
  nama: string;
  nik: string;
  user_level: string;
  fungsi: string | null;
  is_active: boolean;
};

export type UserForm = {
  nama: string;
  nik: string;
  user_level: "admin" | "pjk" | "supervisor" | "ka_bps" | "humas";
  fungsi: string | null;
  is_active: boolean;
  password?: string | null;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};
