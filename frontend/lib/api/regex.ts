const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://localhost:8443'

export type Pattern = {
    pattern_seq: number
    pattern_name: string
    regex_pattern: string
    is_active: boolean
}

export type PatternsResponse = {
    patterns: Pattern[]
}

export async function getAllPatterns(): Promise<Pattern[]> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/read_all_patterns`, {
            method: 'POST',
            headers,
            body: JSON.stringify({}),
        })

        if (!response.ok) {
            throw new Error('Failed to fetch patterns')
        }

        const data: PatternsResponse = await response.json()
        return data.patterns || []
    } catch (error) {
        console.error('[v0] Error fetching patterns:', error)
        return []
    }
}

export async function createPattern(
    pattern_name: string,
    regex_pattern: string
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/create_pattern`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                pattern_name,
                regex_pattern,
            }),
        })

        if (!response.ok) {
            throw new Error('Failed to create pattern')
        }

        const result = await response.json()
        return result === 1
    } catch (error) {
        console.error('[v0] Error creating pattern:', error)
        return false
    }
}

export async function updatePattern(
    pattern_seq: number,
    pattern_name: string,
    regex_pattern: string,
    is_active: boolean
): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/update_pattern`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                pattern_seq,
                pattern_name,
                regex_pattern,
                is_active,
            }),
        })

        if (!response.ok) {
            throw new Error('Failed to update pattern')
        }

        const result = await response.json()
        return result === 1
    } catch (error) {
        console.error('[v0] Error updating pattern:', error)
        return false
    }
}

export async function deletePattern(pattern_seq: number): Promise<boolean> {
    try {
        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/delete_pattern`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                pattern_seq,
            }),
        })

        if (!response.ok) {
            throw new Error('Failed to delete pattern')
        }

        const result = await response.json()
        return result === 1
    } catch (error) {
        console.error('[v0] Error deleting pattern:', error)
        return false
    }
}
