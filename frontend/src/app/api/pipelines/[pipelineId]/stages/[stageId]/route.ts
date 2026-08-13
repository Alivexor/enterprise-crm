import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ pipelineId: string; stageId: string }> };
function stagePath(pipelineId: string, stageId: string): string { return `/pipelines/${encodeURIComponent(pipelineId)}/stages/${encodeURIComponent(stageId)}`; }
export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId, stageId } = await params; return proxyApiRequest(stagePath(pipelineId, stageId), request); }
export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId, stageId } = await params; return proxyApiRequest(stagePath(pipelineId, stageId), request); }
export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId, stageId } = await params; return proxyApiRequest(stagePath(pipelineId, stageId), request); }
