const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://localhost:8443'

export type Category = {
    tag_seq: number
    tag_name: string
    depth: number
    summary: string
    created_at: string
}

export async function getAllCategories(): Promise<Category[]> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/read_all_categories`, {
            method: 'POST',
            headers,
            body: JSON.stringify({}),
        })

        if (!response.ok) {
            console.error('[v0] Failed to fetch categories:', response.statusText)
            return []
        }

        const data = await response.json()
        return data.categories || []
    } catch (error) {
        console.error('[v0] Error fetching categories:', error)
        return []
    }
}

export async function createCategory(
    tag_name: string,
    depth: number,
    summary: string
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/create_category`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                tag_name,
                depth,
                summary,
            }),
        })

        if (!response.ok) {
            console.error('[v0] Failed to create category:', response.statusText)
            return false
        }

        const data = await response.json()
        return data === 1
    } catch (error) {
        console.error('[v0] Error creating category:', error)
        return false
    }
}

export async function updateCategory(
    tag_seq: number,
    tag_name: string,
    depth: number,
    summary: string
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/update_category`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                tag_seq,
                tag_name,
                depth,
                summary,
            }),
        })

        if (!response.ok) {
            console.error('[v0] Failed to update category:', response.statusText)
            return false
        }

        const data = await response.json()
        return data === 1
    } catch (error) {
        console.error('[v0] Error updating category:', error)
        return false
    }
}

export async function deleteCategory(tag_seq: number): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/delete_category`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                tag_seq,
            }),
        })

        if (!response.ok) {
            console.error('[v0] Failed to delete category:', response.statusText)
            return false
        }

        const data = await response.json()
        return data === 1
    } catch (error) {
        console.error('[v0] Error deleting category:', error)
        return false
    }
}
