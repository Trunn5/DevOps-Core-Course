/**
 * Cloudflare Workers Edge API
 * Lab 17 - DevOps Core Course
 */

export interface Env {
	// Environment variables (plaintext)
	APP_NAME: string;
	COURSE_NAME: string;
	VERSION: string;
	
	// Secrets (added via wrangler secret put)
	API_TOKEN?: string;
	ADMIN_EMAIL?: string;
	
	// KV namespace binding
	SETTINGS?: KVNamespace;
}

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		
		// Add CORS headers for all responses
		const corsHeaders = {
			'Access-Control-Allow-Origin': '*',
			'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
			'Access-Control-Allow-Headers': 'Content-Type',
			'Content-Type': 'application/json',
		};
		
		// Handle CORS preflight
		if (request.method === 'OPTIONS') {
			return new Response(null, { headers: corsHeaders });
		}
		
		// Logging for observability
		console.log('Request:', {
			method: request.method,
			path: url.pathname,
			colo: request.cf?.colo,
			country: request.cf?.country,
		});
		
		try {
			// Route: Health check
			if (url.pathname === '/health') {
				return Response.json(
					{
						status: 'ok',
						timestamp: new Date().toISOString(),
						uptime: 'edge-deployed',
					},
					{ headers: corsHeaders }
				);
			}
			
			// Route: Home / API info
			if (url.pathname === '/' || url.pathname === '') {
				return Response.json(
					{
						app: env.APP_NAME,
						course: env.COURSE_NAME,
						version: env.VERSION,
						message: 'Hello from Cloudflare Workers!',
						timestamp: new Date().toISOString(),
						deployment: 'global-edge',
						endpoints: [
							'/',
							'/health',
							'/edge',
							'/counter',
							'/config',
						],
					},
					{ headers: corsHeaders }
				);
			}
			
			// Route: Edge metadata
			if (url.pathname === '/edge') {
				return Response.json(
					{
						// Required fields
						colo: request.cf?.colo || 'unknown',
						country: request.cf?.country || 'unknown',
						
						// Additional fields
						city: request.cf?.city || 'unknown',
						continent: request.cf?.continent || 'unknown',
						timezone: request.cf?.timezone || 'unknown',
						asn: request.cf?.asn || 'unknown',
						httpProtocol: request.cf?.httpProtocol || 'unknown',
						tlsVersion: request.cf?.tlsVersion || 'unknown',
						
						// Request metadata
						userAgent: request.headers.get('user-agent') || 'unknown',
						timestamp: new Date().toISOString(),
					},
					{ headers: corsHeaders }
				);
			}
			
			// Route: Configuration (show plaintext vars and secrets existence)
			if (url.pathname === '/config') {
				return Response.json(
					{
						app: env.APP_NAME,
						course: env.COURSE_NAME,
						version: env.VERSION,
						secrets: {
							apiTokenConfigured: !!env.API_TOKEN,
							adminEmailConfigured: !!env.ADMIN_EMAIL,
						},
						note: 'Secret values are never exposed in responses',
					},
					{ headers: corsHeaders }
				);
			}
			
			// Route: Counter (KV-backed persistence)
			if (url.pathname === '/counter') {
				if (!env.SETTINGS) {
					return Response.json(
						{
							error: 'KV namespace not configured',
							hint: 'Create a KV namespace and bind it to SETTINGS',
						},
						{ status: 500, headers: corsHeaders }
					);
				}
				
				// Get current counter value
				const raw = await env.SETTINGS.get('visits');
				const visits = Number(raw ?? '0') + 1;
				
				// Store incremented value
				await env.SETTINGS.put('visits', String(visits));
				
				// Also store last visit timestamp
				await env.SETTINGS.put('last_visit', new Date().toISOString());
				
				return Response.json(
					{
						visits,
						message: 'Counter persisted in Workers KV',
						note: 'This value survives redeployments',
					},
					{ headers: corsHeaders }
				);
			}
			
			// Route: Not found
			return Response.json(
				{
					error: 'Not Found',
					path: url.pathname,
					availableEndpoints: [
						'/',
						'/health',
						'/edge',
						'/counter',
						'/config',
					],
				},
				{ status: 404, headers: corsHeaders }
			);
		} catch (error) {
			console.error('Error processing request:', error);
			return Response.json(
				{
					error: 'Internal Server Error',
					message: error instanceof Error ? error.message : 'Unknown error',
				},
				{ status: 500, headers: corsHeaders }
			);
		}
	},
};
