import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ dealId: string }> };
function dealPath(dealId: string): string { return `/deals/${encodeURIComponent(dealId)}`; }
export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> { const { dealId } = await params; return proxyApiRequest(dealPath(dealId), request); }
export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> { const { dealId } = await params; return proxyApiRequest(dealPath(dealId), request); }
export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> { const { dealId } = await params; return proxyApiRequest(dealPath(dealId), request); }
