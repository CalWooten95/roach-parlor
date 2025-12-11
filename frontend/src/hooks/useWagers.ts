import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { wagerService, WagerListParams, CreateWagerRequest, UpdateWagerRequest } from '@/services/wagers';
import { WagerStatus } from '@/types';
import { QUERY_KEYS } from '@/utils/constants';

// Hook for fetching paginated wagers
export function useWagers(params: WagerListParams = {}) {
  return useQuery({
    queryKey: [QUERY_KEYS.WAGERS, params],
    queryFn: () => wagerService.getWagers(params),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

// Hook for fetching a single wager
export function useWager(id: number) {
  return useQuery({
    queryKey: [QUERY_KEYS.WAGER, id],
    queryFn: () => wagerService.getWager(id),
    enabled: !!id,
    staleTime: 30000,
  });
}

// Hook for creating a new wager
export function useCreateWager() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (wager: CreateWagerRequest) => wagerService.createWager(wager),
    onSuccess: () => {
      // Invalidate and refetch wagers list
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
    },
  });
}

// Hook for updating a wager
export function useUpdateWager() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: UpdateWagerRequest }) =>
      wagerService.updateWager(id, updates),
    onSuccess: (data, variables) => {
      // Update the specific wager in cache
      queryClient.setQueryData([QUERY_KEYS.WAGER, variables.id], data);
      // Invalidate wagers list to reflect changes
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
    },
  });
}

// Hook for updating wager status
export function useUpdateWagerStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: WagerStatus }) =>
      wagerService.updateWagerStatus(id, status),
    onSuccess: (data, variables) => {
      // Update the specific wager in cache
      queryClient.setQueryData([QUERY_KEYS.WAGER, variables.id], data);
      // Invalidate wagers list to reflect changes
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
    },
  });
}

// Hook for archiving/unarchiving a wager
export function useArchiveWager() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, archived }: { id: number; archived: boolean }) =>
      wagerService.archiveWager(id, archived),
    onSuccess: (data, variables) => {
      // Update the specific wager in cache
      queryClient.setQueryData([QUERY_KEYS.WAGER, variables.id], data);
      // Invalidate wagers list to reflect changes
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
    },
  });
}

// Hook for deleting a wager
export function useDeleteWager() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => wagerService.deleteWager(id),
    onSuccess: (_, id) => {
      // Remove the wager from cache
      queryClient.removeQueries({ queryKey: [QUERY_KEYS.WAGER, id] });
      // Invalidate wagers list to reflect changes
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
    },
  });
}

// Hook for bulk status updates
export function useBulkUpdateStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ids, status }: { ids: number[]; status: WagerStatus }) =>
      wagerService.bulkUpdateStatus(ids, status),
    onSuccess: () => {
      // Invalidate all wager-related queries
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGER] });
    },
  });
}

// Hook for bulk archive operations
export function useBulkArchive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ids, archived }: { ids: number[]; archived: boolean }) =>
      wagerService.bulkArchive(ids, archived),
    onSuccess: () => {
      // Invalidate all wager-related queries
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGER] });
    },
  });
}

// Hook for bulk delete operations
export function useBulkDelete() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => wagerService.bulkDelete(ids),
    onSuccess: (_, ids) => {
      // Remove all deleted wagers from cache
      ids.forEach(id => {
        queryClient.removeQueries({ queryKey: [QUERY_KEYS.WAGER, id] });
      });
      // Invalidate wagers list
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.WAGERS] });
    },
  });
}