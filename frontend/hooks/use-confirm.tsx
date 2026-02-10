"use client"

import { useState, useCallback } from "react"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"

interface ConfirmOptions {
    title?: string
    message: string
    confirmText?: string
    cancelText?: string
    variant?: 'confirm' | 'alert'
}

interface ConfirmState {
    open: boolean
    title: string
    message: string
    confirmText: string
    cancelText: string
    variant: 'confirm' | 'alert'
    resolver?: (value: boolean) => void
}

export function useConfirm() {
    const [state, setState] = useState<ConfirmState>({
        open: false,
        title: "확인",
        message: "",
        confirmText: "예",
        cancelText: "아니오",
        variant: 'confirm',
    })

    const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
        return new Promise((resolve) => {
            setState({
                open: true,
                title: options.title || "확인",
                message: options.message,
                confirmText: options.confirmText || (options.variant === 'alert' ? "확인" : "예"),
                cancelText: options.cancelText || "아니오",
                variant: options.variant || 'confirm',
                resolver: resolve,
            })
        })
    }, [])

    const handleConfirm = useCallback(() => {
        state.resolver?.(true)
        setState((prev) => ({ ...prev, open: false }))
    }, [state.resolver])

    const handleCancel = useCallback(() => {
        state.resolver?.(false)
        setState((prev) => ({ ...prev, open: false }))
    }, [state.resolver])

    const ConfirmDialog = useCallback(
        () => (
            <AlertDialog open={state.open} onOpenChange={(open) => !open && handleCancel()}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>{state.title}</AlertDialogTitle>
                        <AlertDialogDescription>{state.message}</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        {state.variant !== 'alert' && (
                            <AlertDialogCancel onClick={handleCancel}>{state.cancelText}</AlertDialogCancel>
                        )}
                        <AlertDialogAction onClick={handleConfirm}>{state.confirmText}</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        ),
        [state, handleConfirm, handleCancel]
    )

    return { confirm, ConfirmDialog }
}
