extends Node

var udp_server := UDPServer.new()
var peer : PacketPeerUDP
var port := 5055

var current_lane := "center"  # "left", "center", "right"

func _ready():
	udp_server.listen(port)
	print("Listening for UDP on port %d..." % port)

func _process(_delta):
	udp_server.poll()

	# Accept peer if available
	if udp_server.is_connection_available():
		peer = udp_server.take_connection()
		print("New UDP connection accepted")

	# If peer exists and has a packet
	if peer and peer.get_available_packet_count() > 0:
		var data := peer.get_packet().get_string_from_utf8().strip_edges()
		print("Received UDP message: ", data)

		# Update lane if valid
		match data:
			"left", "center", "right":
				current_lane = data
			_:
				print("Unknown lane command: ", data)

func get_lane() -> String:
	return current_lane
