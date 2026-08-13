import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ pipelineId: string }> };
function stagesPath(pipelineId: string): string { return `/pipelines/${encodeURIComponent(pipelineId)}/stages`; }
export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId } = await params; return proxyApiRequest(stagesPath(pipelineId), request); }
export async function POST(request: Request, { params }: RouteContext): Promise<NextResponse> { const { pipelineId } = await params; return proxyApiRequest(stagesPath(pipelineId), request); }
