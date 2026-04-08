#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "IWebSocket.h"
#include "WarSimWebSocketClient.generated.h"

/**
 * WarSimWebSocketClient handles the high-performance link to the Python Simulation.
 * Connects to /ws/ue5/{battle_id} and receives minimized array-based updates.
 */
UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class WARSIM_API UWarSimWebSocketClient : public UActorComponent
{
	GENERATED_BODY()

public:	
	UWarSimWebSocketClient();

	// The Battle ID to track
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WarSim")
	FString BattleId;

	// Server URL (e.g. ws://localhost:8000/ws/ue5/)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WarSim")
	FString ServerUrl = "ws://localhost:8000/ws/ue5/";

	UFUNCTION(BlueprintCallable, Category = "WarSim")
	void Connect();

	UFUNCTION(BlueprintCallable, Category = "WarSim")
	void Disconnect();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	TSharedPtr<IWebSocket> Socket;

	void OnConnected();
	void OnConnectionError(const FString& Error);
	void OnClosed(int32 StatusCode, const FString& Reason, bool bWasClean);
	void OnMessageReceived(const FString& Message);

	// Delegate for Blueprint to handle updates
	DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSimUpdateReceived, const FString&, RawJson);
	UPROPERTY(BlueprintAssignable, Category = "WarSim|Events")
	FOnSimUpdateReceived OnUpdateReceived;
};
