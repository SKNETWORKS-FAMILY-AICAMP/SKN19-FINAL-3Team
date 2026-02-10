const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://localhost:8443'

export type User = {
    user_seq: number
    display_name: string
    username: string
    status_code: 'ACTIVE' | 'INACTIVE'
    created_at: string
}

export type UsersResponse = {
    users: User[]
}

export async function getAllUsers(): Promise<User[]> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/read_all_users`, {
            method: 'POST',
            headers,
            body: JSON.stringify({}),
            cache: 'no-store',
        })

        if (!response.ok) {
            console.error('[v0] Failed to fetch users:', response.status)
            return []
        }

        const data: UsersResponse = await response.json()
        return data.users
    } catch (error) {
        console.error('[v0] Error fetching users:', error)
        return []
    }
}
