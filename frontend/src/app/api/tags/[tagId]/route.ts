import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ tagId: string }> };
function tagPath(tagId: string): string { return `/tags/${encodeURIComponent(tagId)}`; }
export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> { const { tagId } = await params; return proxyApiRequest(tagPath(tagId), request); }
export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> { const { tagId } = await params; return proxyApiRequest(tagPath(tagId), request); }
export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> { const { tagId } = await params; return proxyApiRequest(tagPath(tagId), request); }
