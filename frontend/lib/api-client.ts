export interface RequestOptions extends RequestInit {
    headers?: Record<string, string>;
    skipRedirect?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://localhost:8443";

export class ApiClient {
    private static instance: ApiClient;
    private isRefreshing = false;
    private refreshSubscribers: ((token: string) => void)[] = [];

    private constructor() { }

    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    private onRefreshed(token: string) {
        this.refreshSubscribers.forEach((callback) => callback(token));
        this.refreshSubscribers = [];
    }

    private addRefreshSubscriber(callback: (token: string) => void) {
        this.refreshSubscribers.push(callback);
    }

    public async fetchWithAuth(url: string, options: RequestOptions = {}): Promise<Response> {
        const token = localStorage.getItem("access_token");
        const headers = { ...options.headers };

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            if (!this.isRefreshing) {
                this.isRefreshing = true;

                try {
                    const refreshToken = localStorage.getItem("refresh_token");
                    if (!refreshToken) {
                        throw new Error("No refresh token available");
                    }

                    // Use basic fetch for refresh to avoid infinite loop
                    const refreshResponse = await fetch(`${API_BASE_URL}/api/v1/auth/refresh?refresh_token=${refreshToken}`, {
                        method: "POST",
                    });

                    if (!refreshResponse.ok) {
                        throw new Error("Refresh failed");
                    }

                    const data = await refreshResponse.json();
                    localStorage.setItem("access_token", data.access_token);
                    // Update refresh token if provided, though typically access token is enough
                    if (data.refresh_token) {
                        localStorage.setItem("refresh_token", data.refresh_token);
                    }

                    this.isRefreshing = false;
                    this.onRefreshed(data.access_token);

                    // Retry original request with new token
                    headers["Authorization"] = `Bearer ${data.access_token}`;
                    return fetch(`${API_BASE_URL}${url}`, {
                        ...options,
                        headers,
                    });
                } catch (error) {
                    this.isRefreshing = false;
                    this.handleAuthError(options.skipRedirect);
                    throw error;
                }
            } else {
                // Wait for refresh to complete
                return new Promise((resolve) => {
                    this.addRefreshSubscriber((token: string) => {
                        headers["Authorization"] = `Bearer ${token}`;
                        resolve(fetch(`${API_BASE_URL}${url}`, {
                            ...options,
                            headers,
                        }));
                    });
                });
            }
        }

        return response;
    }

    public async validateToken(): Promise<boolean> {
        try {
            // validateToken은 결과만 반환하고 리다이렉트는 컴포넌트에서 처리하도록 skipRedirect: true 설정
            const response = await this.fetchWithAuth("/api/v1/auth/me", { skipRedirect: true });
            return response.ok;
        } catch (error) {
            console.error("Token validation failed:", error);
            return false;
        }
    }

    private handleAuthError(skipRedirect = false) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        if (skipRedirect) return;

        // Global redirect to login
        if (typeof window !== "undefined") {
            // 무한 루프 방지: 이미 로그인 페이지에 있다면 리다이렉트 하지 않음
            if (!window.location.pathname.includes("/login")) {
                const currentPath = window.location.pathname + window.location.search;
                const redirectParam = currentPath ? `?redirect_url=${encodeURIComponent(currentPath)}` : "";
                window.location.href = `/login${redirectParam}`;
            }
        }
    }
}

export const apiClient = ApiClient.getInstance();
