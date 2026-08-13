import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ pipelineId: string }> };
function pipelinePath(pipelineId: string): string { return `/pipelines/${encodeURIComponent(pipelineId)}`; }
export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId } = await params; return proxyApiRequest(pipelinePath(pipelineId), request); }
export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId } = await params; return proxyApiRequest(pipelinePath(pipelineId), request); }
export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId } = await params; return proxyApiRequest(pipelinePath(pipelineId), request); }
