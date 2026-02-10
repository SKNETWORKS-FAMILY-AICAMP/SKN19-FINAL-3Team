const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://localhost:8443'

export type Permission = {
    recipe_seq: number
    user_seq: number
    role_code: string
    doc_name?: string
    user_name?: string
}

export type PermissionResponse = {
    doc_permissions: Permission[]
}

/**
 * 모든 문서 권한 조회
 */
export async function getAllPermissions(): Promise<Permission[]> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/read_all_doc_permissions`, {
            method: 'POST',
            headers,
            body: JSON.stringify({}),
        })

        if (!response.ok) {
            console.error('[v0] Failed to fetch permissions:', response.status)
            return []
        }

        const data: PermissionResponse = await response.json()
        return data.doc_permissions || []
    } catch (error) {
        console.error('[v0] Error fetching permissions:', error)
        return []
    }
}

/**
 * 문서 권한 생성
 */
export async function createPermission(
    recipe_seq: number,
    user_seq: number,
    role_code: string
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/create_doc_permission`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                recipe_seq,
                user_seq,
                role_code,
            }),
        })

        if (!response.ok) {
            console.error('[v0] Failed to create permission:', response.status)
            return false
        }

        const result = await response.json()
        return result === 1
    } catch (error) {
        console.error('[v0] Error creating permission:', error)
        return false
    }
}

/**
 * 문서 권한 수정
 */
export async function updatePermission(
    recipe_seq: number,
    user_seq: number,
    role_code: string
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/update_doc_permission`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                recipe_seq,
                user_seq,
                role_code,
            }),
        })

        if (!response.ok) {
            console.error('[v0] Failed to update permission:', response.status)
            return false
        }

        const result = await response.json()
        return result === 1
    } catch (error) {
        console.error('[v0] Error updating permission:', error)
        return false
    }
}

/**
 * 문서 권한 삭제
 */
export async function deletePermission(
    recipe_seq: number,
    user_seq: number
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/delete_doc_permission`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                recipe_seq,
                user_seq,
            }),
        })

        if (!response.ok) {
            console.error('[v0] Failed to delete permission:', response.status)
            return false
        }

        const result = await response.json()
        return result === 1
    } catch (error) {
        console.error('[v0] Error deleting permission:', error)
        return false
    }
}
