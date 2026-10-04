package com.saarathi.app.data

object Repository {
    suspend fun compare(req: RouteRequest): CompareResponse {
        return ApiClient.service.compare(req)
    }
}
