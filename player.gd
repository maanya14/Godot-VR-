extends CharacterBody3D

@export var forward_speed := 5.0
@export var lateral_speed := 5.0
@export var jump_velocity := 10.0
@export var lane_width := 3.0
@export var max_lanes := 1  # Use 1 for 3 lanes: -1, 0, 1

var gravity := ProjectSettings.get_setting("physics/3d/default_gravity") as float
var target_x := 0.0
var current_lane := 0  # -1 = left, 0 = center, 1 = right

@onready var facial_input := $"../FacialInput"

func _ready():
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _process(_delta):
	# --- Optional: Keyboard input for testing ---
	if Input.is_action_just_pressed("ui_left"):
		current_lane = clamp(current_lane - 1, -max_lanes, max_lanes)
	elif Input.is_action_just_pressed("ui_right"):
		current_lane = clamp(current_lane + 1, -max_lanes, max_lanes)

	# --- Facial input from UDP ---
	var lane_input: String = facial_input.get_lane()
	match lane_input:
		"left":
			current_lane = -1
		"center":
			current_lane = 0
		"right":
			current_lane = 1

	target_x = current_lane * lane_width

func _physics_process(delta):
	# Apply gravity
	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		# Optional jump
		if Input.is_action_just_pressed("ui_accept"):
			velocity.y = jump_velocity

	# Constant forward movement
	velocity.z = -forward_speed

	# Smooth lateral movement
	var x_diff := target_x - global_position.x
	if abs(x_diff) > 0.05:
		velocity.x = sign(x_diff) * lateral_speed
	else:
		velocity.x = 0.0
		global_position.x = target_x

	move_and_slide()
