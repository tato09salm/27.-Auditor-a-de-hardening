import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./api";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 20_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (error instanceof ApiError && [400, 401, 403, 404, 409, 422].includes(error.status)) {
          return false;
        }
        return failureCount < 1;
      },
    },
    mutations: { retry: 0 },
  },
});
