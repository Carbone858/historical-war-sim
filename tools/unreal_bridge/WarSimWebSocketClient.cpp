#include "WarSimWebSocketClient.h"
#include "WebSocketsModule.h"
#include "Json.h"
#include "Serialization/JsonSerializer.h"

UWarSimWebSocketClient::UWarSimWebSocketClient()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UWarSimWebSocketClient::BeginPlay()
{
	Super::BeginPlay();
	if (!BattleId.IsEmpty())
	{
		Connect();
	}
}

void UWarSimWebSocketClient::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Disconnect();
	Super::EndPlay(EndPlayReason);
}

void UWarSimWebSocketClient::Connect()
{
	if (!FWebSocketsModule::Get().IsModuleLoaded())
	{
		FWebSocketsModule::Get().StartupModule();
	}

	FString FullUrl = ServerUrl + BattleId;
	Socket = FWebSocketsModule::Get().CreateWebSocket(FullUrl, TEXT("ws"));

	Socket->OnConnected().AddUObject(this, &UWarSimWebSocketClient::OnConnected);
	Socket->OnConnectionError().AddUObject(this, &UWarSimWebSocketClient::OnConnectionError);
	Socket->OnClosed().AddUObject(this, &UWarSimWebSocketClient::OnClosed);
	Socket->OnMessage().AddUObject(this, &UWarSimWebSocketClient::OnMessageReceived);

	UE_LOG(LogTemp, Warning, TEXT("WarSim: Connecting to %s"), *FullUrl);
	Socket->Connect();
}

void UWarSimWebSocketClient::Disconnect()
{
	if (Socket.IsValid())
	{
		Socket->Close();
		Socket.Reset();
	}
}

void UWarSimWebSocketClient::OnConnected()
{
	UE_LOG(LogTemp, Warning, TEXT("WarSim: Connected to Simulation Server."));
}

void UWarSimWebSocketClient::OnConnectionError(const FString& Error)
{
	UE_LOG(LogTemp, Error, TEXT("WarSim: Connection Error: %s"), *Error);
}

void UWarSimWebSocketClient::OnClosed(int32 StatusCode, const FString& Reason, bool bWasClean)
{
	UE_LOG(LogTemp, Warning, TEXT("WarSim: Connection Closed. Status: %d, Reason: %s"), StatusCode, *Reason);
}

void UWarSimWebSocketClient::OnMessageReceived(const FString& Message)
{
	// Rapid Dispatch to Multi-threaded or Main-thread processors
	OnUpdateReceived.Broadcast(Message);
}
