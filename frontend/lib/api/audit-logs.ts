const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://localhost:8443'

export type AuditLog = {
    log_seq: number
    operator_seq: number | null
    team_seq: number | null
    task_type_code: string
    task_id: string
    start_task_id: string
    created_at: string
}

export type ReadAuditLogRequest = {
    start_date?: string
    end_date?: string
    task_type_code?: string
    operator_seq?: number
    team_seq?: number
}

export type ReadAuditLogResponse = {
    audit_logs: AuditLog[]
}

export async function getAuditLogs(filters: ReadAuditLogRequest = {}): Promise<AuditLog[]> {
    try {
        // Remove undefined/null values from the request body
        const requestBody: ReadAuditLogRequest = {}

        if (filters.start_date !== undefined && filters.start_date !== null) {
            requestBody.start_date = filters.start_date
        }
        if (filters.end_date !== undefined && filters.end_date !== null) {
            requestBody.end_date = filters.end_date
        }
        if (filters.task_type_code !== undefined && filters.task_type_code !== null && filters.task_type_code !== '') {
            requestBody.task_type_code = filters.task_type_code
        }
        if (filters.operator_seq !== undefined && filters.operator_seq !== null) {
            requestBody.operator_seq = filters.operator_seq
        }
        if (filters.team_seq !== undefined && filters.team_seq !== null) {
            requestBody.team_seq = filters.team_seq
        }

        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/admin/read_audit_log`, {
            method: 'POST',
            headers,
            body: JSON.stringify(requestBody),
            cache: 'no-store',
        })

        if (!response.ok) {
            console.error('[AuditLogs] Failed to fetch audit logs:', response.status)
            return []
        }

        const data: ReadAuditLogResponse = await response.json()
        return data.audit_logs
    } catch (error) {
        console.error('[AuditLogs] Error fetching audit logs:', error)
        return []
    }
}
