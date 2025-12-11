import { apiClient } from './api';
import { Wager, WagerStatus, ApiResponse, PaginatedResponse } from '@/types';
import { API_ENDPOINTS } from '@/utils/constants';

export interface WagerFilters {
  status?: WagerStatus[];
  archived?: boolean;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  sortBy?: 'createdAt' | 'amount' | 'status';
  sortOrder?: 'asc' | 'desc';
}

export interface CreateWagerRequest {
  description: string;
  amount: number;
  line: string;
  isFrePlay?: boolean;
  isLiveBet?: boolean;
  autoCalculate?: boolean;
  liveTrackingEnabled?: boolean;
}

export interface UpdateWagerRequest {
  description?: string;
  amount?: number;
  line?: string;
  status?: WagerStatus;
  isFrePlay?: boolean;
  isLiveBet?: boolean;
  autoCalculate?: boolean;
  liveTrackingEnabled?: boolean;
}

export interface WagerListParams extends WagerFilters {
  page?: number;
  pageSize?: number;
}

export const wagerService = {
  // Get paginated list of wagers
  getWagers: async (params: WagerListParams = {}): Promise<PaginatedResponse<Wager>> => {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('pageSize', params.pageSize.toString());
    if (params.status?.length) queryParams.append('status', params.status.join(','));
    if (params.archived !== undefined) queryParams.append('archived', params.archived.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.dateFrom) queryParams.append('dateFrom', params.dateFrom);
    if (params.dateTo) queryParams.append('dateTo', params.dateTo);
    if (params.sortBy) queryParams.append('sortBy', params.sortBy);
    if (params.sortOrder) queryParams.append('sortOrder', params.sortOrder);

    const url = `${API_ENDPOINTS.WAGERS.LIST}?${queryParams.toString()}`;
    return apiClient.getPaginated<Wager>(url);
  },

  // Get single wager by ID
  getWager: async (id: number): Promise<ApiResponse<Wager>> => {
    return apiClient.get<Wager>(`${API_ENDPOINTS.WAGERS.LIST}/${id}`);
  },

  // Create new wager
  createWager: async (wager: CreateWagerRequest): Promise<ApiResponse<Wager>> => {
    return apiClient.post<Wager>(API_ENDPOINTS.WAGERS.CREATE, wager);
  },

  // Update existing wager
  updateWager: async (id: number, updates: UpdateWagerRequest): Promise<ApiResponse<Wager>> => {
    return apiClient.patch<Wager>(API_ENDPOINTS.WAGERS.UPDATE(id), updates);
  },

  // Update wager status
  updateWagerStatus: async (id: number, status: WagerStatus): Promise<ApiResponse<Wager>> => {
    return apiClient.patch<Wager>(API_ENDPOINTS.WAGERS.STATUS(id), { status });
  },

  // Archive/unarchive wager
  archiveWager: async (id: number, archived: boolean = true): Promise<ApiResponse<Wager>> => {
    return apiClient.patch<Wager>(API_ENDPOINTS.WAGERS.UPDATE(id), { archived });
  },

  // Delete wager
  deleteWager: async (id: number): Promise<ApiResponse<void>> => {
    return apiClient.delete<void>(API_ENDPOINTS.WAGERS.DELETE(id));
  },

  // Bulk operations
  bulkUpdateStatus: async (ids: number[], status: WagerStatus): Promise<ApiResponse<Wager[]>> => {
    return apiClient.patch<Wager[]>(`${API_ENDPOINTS.WAGERS.LIST}/bulk/status`, {
      ids,
      status,
    });
  },

  bulkArchive: async (ids: number[], archived: boolean = true): Promise<ApiResponse<Wager[]>> => {
    return apiClient.patch<Wager[]>(`${API_ENDPOINTS.WAGERS.LIST}/bulk/archive`, {
      ids,
      archived,
    });
  },

  bulkDelete: async (ids: number[]): Promise<ApiResponse<void>> => {
    return apiClient.delete<void>(`${API_ENDPOINTS.WAGERS.LIST}/bulk`, {
      data: { ids },
    });
  },
};