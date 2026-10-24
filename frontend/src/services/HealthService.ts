import { AbstractHttpService } from "./AbstractHttpService";
import { IHealthResponse } from "../types";
import { SystemHealthModel } from "../models";

export interface IHealthService {
  checkHealth(): Promise<SystemHealthModel>;
}

/**
 * Concrete OOP service managing system health queries.
 */
export class HealthService extends AbstractHttpService implements IHealthService {
  constructor(baseUrl: string = "") {
    super(baseUrl);
  }

  public async checkHealth(): Promise<SystemHealthModel> {
    const response = await this.get<IHealthResponse>("/health");
    return SystemHealthModel.fromJson(response);
  }
}
