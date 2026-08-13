import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

export async function POST(request: Request): Promise<NextResponse> {
  return proxyApiRequest("/profile/password", request);
}
