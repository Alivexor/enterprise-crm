import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ noteId: string }> };
function notePath(noteId: string): string { return `/notes/${encodeURIComponent(noteId)}`; }
export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> { const { noteId } = await params; return proxyApiRequest(notePath(noteId), request); }
export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> { const { noteId } = await params; return proxyApiRequest(notePath(noteId), request); }
export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> { const { noteId } = await params; return proxyApiRequest(notePath(noteId), request); }
